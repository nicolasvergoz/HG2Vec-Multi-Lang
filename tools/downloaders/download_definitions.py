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
from downloader import *
from os.path import splitext, isfile, join, exists, basename, dirname
import argparse
import time
import sys
import os

# global variables used (and shared) by all ThreadDown instances
exitFlag = 0
errorFlag = False  # Drapeau pour signaler les erreurs techniques
notFoundLock = Lock()  # Lock pour la liste des mots non trouvés
counterLock = Lock()
errorLock = Lock()  # Lock pour la manipulation du drapeau d'erreur
request_counter  = {"Cam": 0, "Dic": 0, "Col": 0, "Oxf": 0, "robert": 0}
download_counter = {"Cam": 0, "Dic": 0, "Col": 0, "Oxf": 0, "robert": 0}
not_found_words = []  # Liste pour stocker les mots non trouvés, leurs URLs et messages d'erreur

class ThreadDown(Thread):
    """Class representing a thread that download definitions."""
    def __init__(self, dict_name, pos, data_queue, res_queue):
        Thread.__init__(self)
        self.dict_name  = dict_name
        self.pos        = pos # part of speech (noun, verb, adjective or all)
        self.data_queue = data_queue
        self.res_queue  = res_queue

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
                    
                    # Si le résultat est un tuple (None, url, error_msg), c'est un mot non trouvé avec son URL et message d'erreur
                    if isinstance(result, tuple) and result[0] is None:
                        if len(result) >= 3:  # Format avec erreur (None, url, error_msg)
                            # Mot non trouvé - l'enregistrer dans la liste avec son URL et message d'erreur
                            print(f"\nNOTE: No definition found for '{word}' in {self.dict_name} - adding to not-found list with URL and error message")
                            notFoundLock.acquire()
                            not_found_words.append((word, result[1], result[2]))  # Tuple (mot, url, error_msg)
                            notFoundLock.release()
                        else:  # Format avec juste l'URL (None, url)
                            # Mot non trouvé - l'enregistrer dans la liste avec son URL
                            print(f"\nNOTE: No definition found for '{word}' in {self.dict_name} - adding to not-found list with URL")
                            notFoundLock.acquire()
                            not_found_words.append((word, result[1], None))  # Tuple (mot, url, None)
                            notFoundLock.release()
                    elif result is None:
                        # Mot non trouvé - l'enregistrer dans la liste sans URL (pour les dictionnaires autres que Le Robert)
                        print(f"\nNOTE: No definition found for '{word}' in {self.dict_name} - adding to not-found list")
                        notFoundLock.acquire()
                        not_found_words.append((word, None, None))  # Tuple (mot, None, None)
                        notFoundLock.release()
                    elif len(result) > 0:
                        # if len > 0, the downloaded definition contains at least
                        # one word, we can add 1 to the number of downloads
                        counterLock.acquire()
                        download_counter[self.dict_name] += 1
                        counterLock.release()

                        # then add the fetched definition, the word and the
                        # dictionary used as a message for ThreadWrite
                        self.res_queue.put("{} {} {}".format(self.dict_name, word,
                                                           " ".join(result)))
                    else:
                        # Liste vide - pas de définition mais pas d'erreur technique
                        print(f"\nNOTE: Empty definition found for '{word}' in {self.dict_name} - adding to not-found list")
                        notFoundLock.acquire()
                        not_found_words.append((word, None, "Définition vide"))  # Tuple (mot, None, erreur)
                        notFoundLock.release()
                except Exception as e:
                    # Ne pas arrêter le processus, juste logguer l'erreur et continuer
                    error_message = f"Exception technique: {str(e)}"
                    print(f"\nWARNING: Failed to download definition for '{word}' from {self.dict_name}")
                    print(f"Exception: {str(e)}")
                    print("Continuing with next word...")
                    
                    # Ajouter à la liste des mots non trouvés avec le message d'erreur
                    notFoundLock.acquire()
                    not_found_words.append((word, None, error_message))
                    notFoundLock.release()
                    
                    # Ne pas mettre errorFlag à True pour ne pas arrêter les autres threads
                    # On continue simplement avec le mot suivant

class ThreadWrite(Thread):
    """Class representing a thread that write definitions to a file."""
    def __init__(self, filename, msg_queue):
        Thread.__init__(self)
        self.msg_queue = msg_queue
        self.of = open(filename, "a")

    def run(self):
        global exitFlag
        while not exitFlag:
            if not self.msg_queue.empty():
                msg = self.msg_queue.get()
                self.of.write(msg + "\n")

        # Vider la queue avant de terminer
        while True:
            try:
                msg = self.msg_queue.get(True, 5)
                self.of.write(msg + "\n")
            except:
                break

        self.of.close()

def main(filename, pos="all", lang="en", output_dir="data/output/definitions"):
    # 0. to measure download time; use `global` to be able to modify exitFlag
    globalStart = time.time()
    global exitFlag, errorFlag, not_found_words

    # 1. read the file to get the list of words to download definitions
    vocabulary = set()
    with open(filename) as f:
        for line in f:
            vocabulary.add(line.strip())

    vocabulary_size = len(vocabulary)
    print("Reading file {}: Done".format(filename))
    print("Vocabulary size:", vocabulary_size)
    print("Language:", "French" if lang == "fr" else "English")

    # Create output directory if it doesn't exist
    if not exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # add "-definitions" before the file extension to create output filename.
    # If pos is noun/verb/adjective, add it also to the output filename
    # Also add language suffix
    input_filename = basename(filename)
    if pos in ["noun", "verb", "adjective"]:
        output_fn = join(output_dir, splitext(input_filename)[0] + "-definitions-{}-{}.txt".format(pos, lang))
    else:
        output_fn = join(output_dir, splitext(input_filename)[0] + "-definitions-{}.txt".format(lang))
    
    # Create filename for not found words
    not_found_fn = join(output_dir, splitext(input_filename)[0] + "-not-found-{}.txt".format(lang))

    # look if some definitions have already been downloaded. If that's the case,
    # add the words present in output_fn in the aleady_done variable
    already_done = {"Cam": set(), "Dic": set(), "Col": set(), "Oxf": set(), "robert": set()}
    reusing = False
    if isfile(output_fn): # need to read the file, first test if it exists
        with open(output_fn) as f:
            for line in f:
                line = line.split()
                # line[0] is dictionary name, line[1] the word (already) fetched
                if len(line) < 2:
                    continue
                already_done[line[0]].add(line[1])
                reusing = True
    if reusing:
        print("\nSome definitions have already been downloaded into {}.".format(
            output_fn))
        print("Reusing: ")
        for dic in already_done:
            if len(already_done[dic]) > 0:
                print("  - {} definitions from {}".format(
                    len(already_done[dic]), dic))

    # 2. create queues containing all words to fetch (queues depend on language)
    # The words to download are in queue_{Cam, Dic, Col, Oxf, Robert}, the downloaded
    # definitions are pushed in queue_msg
    queue_Cam = Queue() if lang == "en" else None
    queue_Dic = Queue() if lang == "en" else None
    queue_Col = Queue() if lang == "en" else None
    queue_Oxf = Queue() if lang == "en" else None
    queue_Robert = Queue() if lang == "fr" else None
    queue_msg = Queue()

    # only add words in queue if they are not already done and the queue exists (depends on language)
    for w in vocabulary:
        if lang == "en":
            if queue_Cam and not w in already_done["Cam"]:
                queue_Cam.put(w)
            if queue_Dic and not w in already_done["Dic"]:
                queue_Dic.put(w)
            if queue_Col and not w in already_done["Col"]:
                queue_Col.put(w)
            if queue_Oxf and not w in already_done["Oxf"]:
                queue_Oxf.put(w)
        elif lang == "fr":
            if queue_Robert and not w in already_done["robert"]:
                queue_Robert.put(w)

    # 3. create threads
    threads = []
    thread_writer = ThreadWrite(output_fn, queue_msg)
    thread_writer.start()
    threads.append(thread_writer)

    # Adjust thread count based on dictionaries used
    NB_THREAD = cpu_count() * 3
    
    # Create appropriate threads based on language
    if lang == "en":
        print("\nDownloading definitions from English dictionaries...")
        for x in range(NB_THREAD):
            if queue_Cam:
                thread_Cam = ThreadDown("Cam", pos, queue_Cam, queue_msg)
                thread_Cam.start()
                threads.append(thread_Cam)
            if queue_Dic:
                thread_Dic = ThreadDown("Dic", pos, queue_Dic, queue_msg)
                thread_Dic.start()
                threads.append(thread_Dic)
            if queue_Col:
                thread_Col = ThreadDown("Col", pos, queue_Col, queue_msg)
                thread_Col.start()
                threads.append(thread_Col)
            if queue_Oxf:
                thread_Oxf = ThreadDown("Oxf", pos, queue_Oxf, queue_msg)
                thread_Oxf.start()
                threads.append(thread_Oxf)
    elif lang == "fr":
        print("\nDownloading definitions from Le Robert (French dictionary)...")
        for x in range(NB_THREAD * 4):  # Use all available threads for Robert since it's the only one
            if queue_Robert:
                thread_Robert = ThreadDown("robert", pos, queue_Robert, queue_msg)
                thread_Robert.start()
                threads.append(thread_Robert)

    # 4. monitor threads and check for errors, show progress
    percent = 0
    
    # Wait for threads to complete
    try:
        # Continue checking while threads are running
        if lang == "en":
            while (not queue_msg.empty() or
                  (queue_Cam and not queue_Cam.empty()) or
                  (queue_Dic and not queue_Dic.empty()) or
                  (queue_Col and not queue_Col.empty()) or
                  (queue_Oxf and not queue_Oxf.empty())):

                # For English: 4 dictionaries
                tmp = sum(request_counter.values()) / (4.0 * vocabulary_size) * 100
                tmp = int(tmp) + 1
                if tmp != percent:
                    print('\r{0}%'.format(tmp), end="")
                    percent = tmp
                
                # Dormir un peu pour éviter de surcharger le CPU
                time.sleep(0.1)
                
        elif lang == "fr":
            while (not queue_msg.empty() or
                  (queue_Robert and not queue_Robert.empty())):

                # For French: 1 dictionary only
                tmp = request_counter["robert"] / (1.0 * vocabulary_size) * 100
                tmp = int(tmp) + 1
                if tmp != percent:
                    print('\r{0}%'.format(tmp), end="")
                    percent = tmp
                    
                # Dormir un peu pour éviter de surcharger le CPU
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
    print("Total time: {:.2f} sec\n".format(time.time() - globalStart))
    
    # Écrire les mots non trouvés dans un fichier séparé
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
                    # Pour la compatibilité avec l'ancien format
                    nf.write(f"{item}\n")
        print(f"Words without definitions: {len(not_found_words)}")
        print(f"List of words without definitions written to: {not_found_fn}")
    
    print("S T A T S (# successful download / # requests)")
    print("==============================================")
    
    # Only show statistics for dictionaries used in the current language
    if lang == "en":
        relevant_dicts = ["Cam", "Dic", "Col", "Oxf"]
    else:
        relevant_dicts = ["robert"]
        
    for dic in sorted(request_counter.keys()):
        if dic in relevant_dicts and request_counter[dic] > 0:
            print("{}   {}/{}".format(
                    dic, download_counter[dic], request_counter[dic]),
                    end="")
            print("  ({:.1f}%)".format(
                download_counter[dic] * 100 / request_counter[dic]))

    print("\n-> Results written in", output_fn)

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
        which dictionaries to use. EN uses Cambridge, Dictionary.com, Collins, and
        Oxford. FR uses only Le Robert.""", type=str.lower, default="en")
    parser.add_argument("-out", "--output_dir", help="""Output directory for definition files.
        Default is 'data/output/definitions'""", 
        default="data/output/definitions")
    args = parser.parse_args()

    if args.pos not in ["noun", "verb", "adjective", "all"]:
        print("WARNING: invalid POS argument \"{}\"".format(args.pos))
        print("It can be NOUN, VERB or ADJECTIVE. Using default POS (ALL)\n")
        args.pos = "all"
        
    if args.lang not in ["en", "fr"]:
        print("WARNING: invalid LANG argument \"{}\"".format(args.lang))
        print("It can be EN or FR. Using default language (EN)\n")
        args.lang = "en"

    main(args.list_words, pos=args.pos, lang=args.lang, output_dir=args.output_dir)
