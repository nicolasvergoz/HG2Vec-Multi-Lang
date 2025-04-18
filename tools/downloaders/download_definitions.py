#!/usr/bin/env python3
#
# Copyright (c) 2017-present, All rights reserved.
# Written by Julien Tissier <30314448+tca19@users.noreply.github.com>
#
# This file is part of Dict2vec.
#
# Dict2vec is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Dict2vec is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License at the root of this repository for
# more details.
#
# You should have received a copy of the GNU General Public License
# along with Dict2vec.  If not, see <http://www.gnu.org/licenses/>.

from queue import Queue
from threading import Thread, Lock
from multiprocessing import cpu_count
from downloader import download_word_definition
from dictionaries import get_language_downloaders, DictionaryDownloader
from os.path import splitext, isfile, join, exists, basename, dirname
import argparse
import time
import sys
import os
import re

# Import the clean_defs function from clean_definitions.py
from clean_definitions import clean_defs

# global variables used (and shared) by all ThreadDown instances
exitFlag = 0
errorFlag = False  # Flag to signal technical errors
notFoundLock = Lock()  # Lock for the list of words not found
counterLock = Lock()
errorLock = Lock()  # Lock for error flag manipulation
# Initialize counters with standard short codes
request_counter = {}
download_counter = {}
not_found_words = []  # List to store words not found, their URLs and error messages

class ThreadDown(Thread):
    """Class representing a thread that download definitions."""
    def __init__(self, dict_name, pos, data_queue, res_queue, ignore_warnings=False):
        Thread.__init__(self)
        self.dict_name  = dict_name
        self.pos        = pos # part of speech (noun, verb, adjective or all)
        self.data_queue = data_queue
        self.res_queue  = res_queue
        self.ignore_warnings = ignore_warnings

    def run(self):
        global exitFlag, errorFlag, not_found_words
        while not exitFlag:
            if not self.data_queue.empty():
                word = self.data_queue.get()
                try:
                    result = download_word_definition(self.dict_name, word, self.pos)
                    
                    counterLock.acquire()
                    request_counter[self.dict_name] += 1
                    counterLock.release()
                    
                    # If the result is a tuple (None, url, error_msg), it's a word not found with its URL and error message
                    if isinstance(result, tuple) and result[0] is None:
                        if len(result) >= 3:  # Format with error (None, url, error_msg)
                            # Word not found - add it to the list with its URL and error message
                            if not self.ignore_warnings:
                                print(f"\nNOTE: No definition found for '{word}' in {self.dict_name} - adding to not-found list with URL and error message")
                                notFoundLock.acquire()
                                not_found_words.append((word, result[1], result[2]))  # Tuple (word, url, error_msg)
                                notFoundLock.release()
                            else:
                                print(f"\nSkipping '{word}' (no definition found in {self.dict_name})")
                        else:  # Format with just the URL (None, url)
                            # Word not found - add it to the list with its URL
                            if not self.ignore_warnings:
                                print(f"\nNOTE: No definition found for '{word}' in {self.dict_name} - adding to not-found list with URL")
                                notFoundLock.acquire()
                                not_found_words.append((word, result[1], None))  # Tuple (word, url, None)
                                notFoundLock.release()
                            else:
                                print(f"\nSkipping '{word}' (no definition found in {self.dict_name})")
                    elif result is None:
                        # Word not found - add it to the list without URL (for dictionaries other than Le Robert)
                        if not self.ignore_warnings:
                            print(f"\nNOTE: No definition found for '{word}' in {self.dict_name} - adding to not-found list")
                            notFoundLock.acquire()
                            not_found_words.append((word, None, None))  # Tuple (word, None, None)
                            notFoundLock.release()
                        else:
                            print(f"\nSkipping '{word}' (no definition found in {self.dict_name})")
                    elif len(result) > 0:
                        # if len > 0, the downloaded definition contains at least
                        # one word, we can add 1 to the number of downloads
                        counterLock.acquire()
                        download_counter[self.dict_name] += 1
                        counterLock.release()

                        # then add the fetched definition, the word and the
                        # dictionary used as a message for ThreadWrite
                        # Format without dictionary prefix
                        self.res_queue.put("{} {}".format(word, " ".join(result)))
                    else:
                        # Empty list - no definition but no technical error
                        if not self.ignore_warnings:
                            print(f"\nNOTE: Empty definition found for '{word}' in {self.dict_name} - adding to not-found list")
                            notFoundLock.acquire()
                            not_found_words.append((word, None, "Empty definition"))  # Tuple (word, None, error)
                            notFoundLock.release()
                        else:
                            print(f"\nSkipping '{word}' (empty definition in {self.dict_name})")
                except Exception as e:
                    # Don't stop the process, just log the error and continue
                    error_message = f"Technical exception: {str(e)}"
                    print(f"\nWARNING: Failed to download definition for '{word}' from {self.dict_name}")
                    print(f"Exception: {str(e)}")
                    print("Continuing with next word...")
                    
                    # Add to the list of words not found with the error message
                    if not self.ignore_warnings:
                        notFoundLock.acquire()
                        not_found_words.append((word, None, error_message))
                        notFoundLock.release()
                    else:
                        print(f"Skipping '{word}' due to technical error")
                    
                    # Don't set errorFlag to True to avoid stopping other threads
                    # Just continue with the next word

class ThreadWrite(Thread):
    """Class representing a thread that write definitions to a file."""
    def __init__(self, filename, msg_queue):
        Thread.__init__(self)
        self.msg_queue = msg_queue
        self.of = open(filename, "a")
        self.counter = 0  # Counter to track number of definitions written

    def run(self):
        global exitFlag
        while not exitFlag:
            if not self.msg_queue.empty():
                msg = self.msg_queue.get()
                self.of.write(msg + "\n")
                self.counter += 1
                
                # Flush the file every 100 definitions
                if self.counter % 100 == 0:
                    self.of.flush()
                    print(f"\r{self.counter} definitions written to file", end="")

        # Empty the queue before terminating
        while True:
            try:
                msg = self.msg_queue.get(True, 5)
                self.of.write(msg + "\n")
                self.counter += 1
                
                # Flush one last time if needed
                if self.counter % 100 == 0:
                    self.of.flush()
                    print(f"\r{self.counter} definitions written to file", end="")
            except:
                break

        # Final flush to ensure all data is written
        self.of.flush()
        print(f"\nTotal: {self.counter} definitions written to file")
        self.of.close()

def main(filename, pos="all", lang="en", output_dir="data/output/definitions", min_word_length=1, use_stopwords=True, stopwords_file=None, max_iterations=1, max_definitions=None, ignore_warnings=False):
    # 0. to measure download time; use `global` to be able to modify exitFlag
    globalStart = time.time()
    global exitFlag, errorFlag, not_found_words, request_counter, download_counter
    
    # Use temp directory during processing
    temp_dir = "data/temp/definitions"
    if not exists(temp_dir):
        os.makedirs(temp_dir)
        print(f"Created temporary directory: {temp_dir}")

    # 1. read the file to get the list of words to download definitions
    vocabulary = set()
    with open(filename) as f:
        for line in f:
            vocabulary.add(line.strip())

    vocabulary_size = len(vocabulary)
    original_vocabulary_size = vocabulary_size
    print("Reading file {}: Done".format(filename))
    print("Initial vocabulary size:", vocabulary_size)
    print("Language:", "French" if lang == "fr" else "English")

    # Determine the location of stopwords file based on language
    final_stopwords_file = stopwords_file
    if use_stopwords and not final_stopwords_file:
        # Base path for stopwords files - try different common locations
        potential_paths = [
            join("data", "input", f"stopwords_{lang}.txt"),  # Current project structure
            join(dirname(dirname(dirname(__file__))), "data", "input", f"stopwords_{lang}.txt"),  # Relative to script
            join(os.path.expanduser("~"), "Side", "HG2VecMulti", "data", "input", f"stopwords_{lang}.txt")  # Absolute path
        ]
        
        for path in potential_paths:
            if isfile(path):
                final_stopwords_file = path
                print(f"Using stopwords file: {final_stopwords_file}")
                break
        
        if not final_stopwords_file:
            print(f"WARNING: {lang.upper()} stopwords file not found")
    elif final_stopwords_file:
        print(f"Using specified stopwords file: {final_stopwords_file}")
    elif not use_stopwords:
        print("Stopwords filtering disabled")
    
    # Track all downloaded definitions to avoid duplicates across iterations
    all_processed_words = set()
    all_definitions_count = 0
    
    # For each iteration
    current_iteration = 1
    input_file = filename
    
    while current_iteration <= max_iterations:
        # Vérifier si on a atteint le nombre maximum de définitions avant de commencer l'itération
        if max_definitions and all_definitions_count >= max_definitions:
            print(f"\nReached maximum number of definitions ({max_definitions})")
            break
            
        print(f"\n===== Iteration {current_iteration}/{max_iterations} =====")
        print(f"Current vocabulary size: {len(vocabulary)}")
        
        # Generate iteration-specific filenames
        input_filename = basename(input_file)
        
        # Check if the input filename already has an iteration prefix
        if input_filename.startswith("iter"):
            # Extract the part after the iteration prefix
            match = re.match(r'iter\d+-(.+)', input_filename)
            if match:
                base_name = match.group(1)
            else:
                base_name = splitext(input_filename)[0]
        else:
            base_name = splitext(input_filename)[0]
            
        if pos in ["noun", "verb", "adjective"]:
            output_fn = join(temp_dir, f"iter{current_iteration}-{base_name}-definitions-{pos}.txt")
        else:
            output_fn = join(temp_dir, f"iter{current_iteration}-{base_name}-definitions.txt")
        
        # Create filename for not found words
        not_found_fn = join(temp_dir, f"iter{current_iteration}-{base_name}-not-found.txt")

        # Create filename for cleaned definitions - without the "iter<N>-" prefix
        clean_output_fn = join(temp_dir, f"{splitext(basename(output_fn))[0].replace(f'iter{current_iteration}-', '')}-clean.txt")
        
        # Filename for accumulated definitions (preserved between iterations)
        accumulated_clean_fn = join(temp_dir, "accumulated-definitions-clean.txt")
        
        # Reset counter for this iteration
        not_found_words = []

        # Get the dictionary downloaders for the specified language
        language_downloaders = get_language_downloaders(lang)
        
        # Initialize counters for each dictionary
        for downloader in language_downloaders.values():
            request_counter[downloader.short_code] = 0
            download_counter[downloader.short_code] = 0
        
        # look if some definitions have already been downloaded. If that's the case,
        # add the words present in output_fn in the aleady_done variable
        already_done = {downloader.short_code: set() for downloader in language_downloaders.values()}
        # Add all previously processed words
        for downloader in language_downloaders.values():
            already_done[downloader.short_code].update(all_processed_words)
            
        reusing = False
        if isfile(output_fn): # need to read the file, first test if it exists
            with open(output_fn) as f:
                for line in f:
                    line = line.split()
                    # In the new format, line[0] is the word directly (no dictionary prefix)
                    if len(line) < 1:
                        continue
                    # Add the word to all dictionaries' already_done sets
                    word = line[0]
                    for dict_code in already_done:
                        already_done[dict_code].add(word)
                        reusing = True
        if reusing:
            print("\nSome definitions have already been downloaded into {}.".format(
                output_fn))
            print("Reusing: ")
            for dic in already_done:
                if len(already_done[dic]) > 0:
                    print("  - {} definitions from {}".format(
                        len(already_done[dic]), dic))

        # 2. create queues containing all words to fetch based on available dictionaries
        queues = {downloader.short_code: Queue() for downloader in language_downloaders.values()}
        queue_msg = Queue()

        # Only add words in queue if they are not already done
        for w in vocabulary:
            for downloader in language_downloaders.values():
                dict_code = downloader.short_code
                if w not in already_done[dict_code]:
                    queues[dict_code].put(w)
                    # Track all words being processed
                    all_processed_words.add(w)

        # 3. create threads
        threads = []
        thread_writer = ThreadWrite(output_fn, queue_msg)
        thread_writer.start()
        threads.append(thread_writer)

        # Adjust thread count based on dictionaries used
        NB_THREAD = cpu_count() * 3
        
        # Calculate threads per dictionary
        nb_dicts = len(language_downloaders)
        if nb_dicts > 0:
            threads_per_dict = max(1, NB_THREAD // nb_dicts)
        else:
            print(f"ERROR: No dictionaries available for language '{lang}'")
            exitFlag = 1
            thread_writer.join()
            return
        
        # Create threads for each dictionary
        print(f"\nDownloading definitions using {threads_per_dict} threads per dictionary...")
        for downloader in language_downloaders.values():
            dict_code = downloader.short_code
            print(f"  - Using {downloader.name} dictionary (code: {dict_code})")
            for _ in range(threads_per_dict):
                thread = ThreadDown(dict_code, pos, queues[dict_code], queue_msg, ignore_warnings)
                thread.start()
                threads.append(thread)

        # 4. monitor threads and check for errors, show progress
        percent = 0
        
        # Wait for threads to complete
        try:
            # Continue checking while threads are running
            while True:
                # Check if all queues are empty
                all_queues_empty = all(q.empty() for q in queues.values()) and queue_msg.empty()
                if all_queues_empty:
                    break
                
                # Check if we have reached the maximum number of definitions
                current_definitions_count = sum(download_counter.values())
                if max_definitions and (all_definitions_count + current_definitions_count) >= max_definitions:
                    print(f"\nMaximum number of definitions reached ({max_definitions})")
                    # Arrêter tous les threads de téléchargement
                    exitFlag = 1
                    break
                    
                # Calculate progress based on requests processed
                if nb_dicts > 0:
                    total_requests = sum(request_counter[code] for code in queues.keys())
                    progress = total_requests / (nb_dicts * len(vocabulary)) * 100
                    tmp = int(progress) + 1
                    if tmp != percent:
                        print('\r{0}%'.format(tmp), end="")
                        percent = tmp
                
                # Sleep a bit to avoid overloading the CPU
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nKeyboard interrupt detected. Stopping all threads...")
            # Seule l'interruption clavier doit arrêter le processus
        
        exitFlag = 1
        # we only wait thread_writer to join because this is the most important
        # thread in the code and we are only interested in what the program
        # is writing.
        print("\nWaiting thread_writer to join.")
        thread_writer.join()

        # 5. get total time and some results infos.
        print("Iteration time: {:.2f} sec\n".format(time.time() - globalStart))
        
        # Write the words not found in a separate file
        if len(not_found_words) > 0:
            with open(not_found_fn, "w") as nf:
                for item in not_found_words:
                    if isinstance(item, tuple):
                        if len(item) >= 3:  # Format (mot, url, error_msg)
                            word, url, error_msg = item
                            if url and error_msg:
                                nf.write(f"{word} {url} # {error_msg}\n")
                            elif url:
                                nf.write(f"{word} {url}\n")
                            elif error_msg:
                                nf.write(f"{word} # {error_msg}\n")
                            else:
                                nf.write(f"{word}\n")
                        elif len(item) == 2:  # Format (mot, url)
                            word, url = item
                            if url:
                                nf.write(f"{word} {url}\n")
                            else:
                                nf.write(f"{word}\n")
                        else:  # Format simple (mot)
                            nf.write(f"{item[0]}\n")
                    else:
                        # For compatibility with the old format
                        nf.write(f"{item}\n")
            print(f"Words without definitions: {len(not_found_words)}")
            print(f"List of words without definitions written to: {not_found_fn}")
        
        print("S T A T S (# successful download / # requests)")
        print("==============================================")
        
        # Only show statistics for dictionaries used
        for downloader in language_downloaders.values():
            dict_code = downloader.short_code
            if request_counter[dict_code] > 0:
                print("{}   {}/{}".format(
                        dict_code, download_counter[dict_code], request_counter[dict_code]),
                        end="")
                print("  ({:.1f}%)".format(
                    download_counter[dict_code] * 100 / request_counter[dict_code]))
                # Add to total count
                all_definitions_count += download_counter[dict_code]

        print("\n-> Raw definitions written in", output_fn)
        
        # Clean the definitions and create a new file with the cleaned definitions
        print("\nCleaning definitions...")
        clean_defs(output_fn, clean_output_fn, "", min_word_length, final_stopwords_file)
        print(f"-> Cleaned definitions written in {clean_output_fn}")
        
        # Merge cleaned definitions with accumulated definitions from previous iterations
        print("\nMerging with definitions from previous iterations...")
        all_definitions = {}  # Dictionary to store all definitions (word -> definition)
        
        # Read existing definitions if they exist
        if isfile(accumulated_clean_fn):
            with open(accumulated_clean_fn, 'r') as f:
                for line in f:
                    parts = line.strip().split(' ', 1)  # Split the word and its definition
                    if len(parts) >= 2:
                        word, definition = parts
                        all_definitions[word] = definition
            print(f"Loaded {len(all_definitions)} existing definitions from {accumulated_clean_fn}")
        
        # Add new definitions
        new_definitions_count = 0
        with open(clean_output_fn, 'r') as f:
            for line in f:
                parts = line.strip().split(' ', 1)  # Split the word and its definition
                if len(parts) >= 2:
                    word, definition = parts
                    if word not in all_definitions:
                        new_definitions_count += 1
                    all_definitions[word] = definition
        
        # Write all merged definitions
        with open(accumulated_clean_fn, 'w') as f:
            for word, definition in all_definitions.items():
                f.write(f"{word} {definition}\n")
        
        print(f"Added {new_definitions_count} new definitions")
        print(f"-> {len(all_definitions)} total definitions written to {accumulated_clean_fn}")
        
        # For next iteration, extract new words from cleaned definitions if not the last iteration
        if current_iteration < max_iterations and (not max_definitions or all_definitions_count < max_definitions):
            print("\nExtracting new words for the next iteration...")
            new_vocabulary = set()
            original_words = set()
            
            # Collect words from accumulated definitions instead of the current iteration file
            with open(accumulated_clean_fn, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 1:
                        original_words.add(parts[0])  # The defined word
                        if len(parts) >= 2:
                            new_vocabulary.update(parts[1:])  # The words in the definition
            
            # Filter out already processed words
            new_vocabulary = (new_vocabulary - all_processed_words)
            
            # Create a temporary file for the new vocabulary
            # Replace existing iteration prefix instead of adding it
            base_filename = basename(input_file)
            # Check if the filename already has an iteration prefix
            if base_filename.startswith(f"iter"):
                # Extract the part after the iteration prefix (after "iter<n>-")
                match = re.match(r'iter\d+-(.+)', base_filename)
                if match:
                    base_name = match.group(1)
                    next_input_file = join(temp_dir, f"iter{current_iteration+1}-{base_name}")
                else:
                    # Fallback if the pattern doesn't match
                    next_input_file = join(temp_dir, f"iter{current_iteration+1}-vocabulary.txt")
            else:
                # No iteration prefix, add the new one
                next_input_file = join(temp_dir, f"iter{current_iteration+1}-{base_filename}")
            
            with open(next_input_file, 'w') as f:
                for word in new_vocabulary:
                    f.write(f"{word}\n")
            
            print(f"Found {len(new_vocabulary)} new words for next iteration")
            print(f"New vocabulary written to {next_input_file}")
            
            # Update for next iteration
            vocabulary = new_vocabulary
            input_file = next_input_file
        
        # Reset exitFlag for next iteration
        exitFlag = 0
        current_iteration += 1
    
    # Move final files to output directory if they don't exist yet
    if not exists(output_dir):
        os.makedirs(output_dir)
    
    # Copy final accumulated definitions file to output directory
    final_definitions = join(output_dir, splitext(basename(filename))[0] + "-definitions.txt")
    
    import shutil
    if accumulated_clean_fn and isfile(accumulated_clean_fn):
        shutil.copy2(accumulated_clean_fn, final_definitions)
        print(f"\nFinal accumulated definitions copied to: {final_definitions}")
    
    total_time = time.time() - globalStart
    print(f"\nVocabulary expansion complete:")
    print(f"  - Started with: {original_vocabulary_size} words")
    print(f"  - Total definitions: {all_definitions_count}")
    print(f"  - Total iterations completed: {current_iteration - 1}")
    print(f"  - Total processing time: {total_time:.2f} seconds")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("list_words", metavar="list-words",
        help="""File containing a list of words (one per line). The script will
        download the definitions for each word.""")
    parser.add_argument("-pos", help="""Either NOUN/VERB/ADJECTIVE. If POS (Part
        Of Speech) is given, the script will only download the definitions that
        corresponds to that POS, not the other ones. By default, it downloads
        the definitions for all POS""", type=str.lower, default="all")
    parser.add_argument("-lang", help="""Either EN (English) or FR (French). Determines
        which dictionaries to use. EN uses Cambridge, Dictionary.com, and Collins. FR uses only Le Robert.""", type=str.lower, default="en")
    parser.add_argument("-out", "--output_dir", help="""Output directory for final definition files.
        Default is 'data/output/definitions'""", 
        default="data/output/definitions")
    parser.add_argument("-l", "--min-length", help="""Minimum word length to keep in definitions (default: 1)""",
        type=int, default=1)
    parser.add_argument("--no-stopwords", help="""Do not filter out stopwords""",
        action="store_true", default=False)
    parser.add_argument("-s", "--stopwords", help="""Path to a specific stopwords file. 
        If not specified, will look for stopwords_[lang].txt in data/input/ directory""",
        default=None)
    parser.add_argument("-i", "--iterations", help="""Number of vocabulary expansion iterations (default: 1)""",
        type=int, default=1)
    parser.add_argument("-m", "--max-definitions", help="""Maximum number of definitions to download across all iterations""",
        type=int, default=None)
    parser.add_argument("--ignore-warnings", help="""Skip words with errors or empty definitions instead of adding them to the not-found list""",
        action="store_true", default=False)
    args = parser.parse_args()

    if args.pos not in ["noun", "verb", "adjective", "all"]:
        print("WARNING: invalid POS argument \"{}\"".format(args.pos))
        print("It can be NOUN, VERB or ADJECTIVE. Using default POS (ALL)\n")
        args.pos = "all"
        
    if args.lang not in ["en", "fr"]:
        print("WARNING: invalid LANG argument \"{}\"".format(args.lang))
        print("It can be EN or FR. Using default language (EN)\n")
        args.lang = "en"

    main(args.list_words, pos=args.pos, lang=args.lang, output_dir=args.output_dir, 
         min_word_length=args.min_length, use_stopwords=not args.no_stopwords, stopwords_file=args.stopwords,
         max_iterations=args.iterations, max_definitions=args.max_definitions,
         ignore_warnings=args.ignore_warnings)
