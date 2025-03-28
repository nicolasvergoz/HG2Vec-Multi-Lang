"""Definition batch processor for retrieving and managing word definitions in bulk.

This module provides higher-level functionality for batch processing of word definitions, 
including multithreaded downloads, file I/O operations, and a command-line interface.
"""

import time
import logging
import argparse
import os
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from hg2vec_multi.tools.downloaders.dictionary_config import ERROR_CODES
from hg2vec_multi.tools.downloaders.definition_fetcher import download_word_definition


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DefinitionDownloader:
    """Class for downloading word definitions from online dictionaries."""
    
    def __init__(self, language: str = "en", 
                 output_dir: Optional[Union[str, Path]] = None):
        """Initialize the definition downloader.
        
        Args:
            language: Language code (en or fr)
            output_dir: Optional output directory
        """
        self.language = language
        self.output_dir = output_dir or os.path.join(os.getcwd(), "definitions")
        
        # Ensure output directory exists
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _download_single_word(self, word: str, pos: str) -> Tuple[str, Dict[str, str]]:
        """Download definition for a single word.
        
        Args:
            word: Word to download definition for
            pos: Part of speech filter
            
        Returns:
            Tuple of (word, definitions dictionary)
        """
        try:
            definitions = download_word_definition(word, pos, self.language)
            if not definitions:
                return word, {"error": ERROR_CODES["not_found"]}
            return word, definitions
            
        except Exception as e:
            logger.error(f"Error downloading {word}: {str(e)}")
            return word, {"error": str(e)}
    
    def download_definitions(self, 
                            word_file: str, 
                            pos: str = "all", 
                            threads: int = 4
                           ) -> Tuple[str, str]:
        """Download definitions for words in a file.
        
        Args:
            word_file: Path to file containing words
            pos: Part of speech filter
            threads: Number of threads to use
            
        Returns:
            Tuple of (definitions_file_path, not_found_file_path)
        """
        # Validate file
        if not os.path.exists(word_file):
            raise FileNotFoundError(f"Word file {word_file} not found")
            
        # Load words
        words = []
        with open(word_file) as f:
            for line in f:
                word = line.strip()
                if word:
                    words.append(word)
                    
        if not words:
            raise ValueError(f"No words found in {word_file}")
            
        # Create output file paths
        input_path = Path(word_file)
        base_name = input_path.stem
        
        definitions_file = self.output_dir / f"{base_name}-definitions-{self.language}.txt"
        not_found_file = self.output_dir / f"{base_name}-not-found-{self.language}.txt"
        
        # Track progress
        total_words = len(words)
        success_count = 0
        not_found_count = 0
        other_errors_count = 0
        
        logger.info(f"Downloading definitions for {total_words} words using {threads} threads")
        
        # Download definitions using threads
        with open(definitions_file, "w") as def_file, open(not_found_file, "w") as nf_file:
            with ThreadPoolExecutor(max_workers=threads) as executor:
                # Submit all tasks
                future_to_word = {
                    executor.submit(self._download_single_word, word, pos): word 
                    for word in words
                }
                
                # Process results as they complete
                for i, future in enumerate(as_completed(future_to_word), 1):
                    word = future_to_word[future]
                    try:
                        _, result = future.result()
                        
                        if "error" in result:
                            error_msg = result["error"]
                            nf_file.write(f"{word}\t{error_msg}\n")
                            
                            if error_msg == ERROR_CODES["not_found"]:
                                not_found_count += 1
                            else:
                                other_errors_count += 1
                        else:
                            # Write definitions to file
                            for dict_name, definition in result.items():
                                def_file.write(f"{dict_name}\t{word}\t{definition}\n")
                            success_count += 1
                        
                        # Log progress
                        if i % 10 == 0 or i == total_words:
                            complete_pct = (i / total_words) * 100
                            logger.info(f"Progress: {i}/{total_words} words ({complete_pct:.1f}%)")
                            
                    except Exception as e:
                        logger.error(f"Error processing {word}: {str(e)}")
                        nf_file.write(f"{word}\t{str(e)}\n")
                        other_errors_count += 1
        
        # Log results
        logger.info(f"Completed: {success_count} successful, {not_found_count} not found, "
                   f"{other_errors_count} other errors")
        logger.info(f"Definitions saved to: {definitions_file}")
        logger.info(f"Not found words saved to: {not_found_file}")
        
        return str(definitions_file), str(not_found_file)


def main(args=None):
    """Command-line interface for downloading definitions."""
    # If no args provided, parse them from command line
    if args is None:
        parser = argparse.ArgumentParser(description="Download word definitions")
        parser.add_argument("word_file", help="File containing words to download definitions for")
        parser.add_argument("-l", "--language", choices=["en", "fr"], default="en",
                            help="Language of the words")
        parser.add_argument("-p", "--pos", choices=["all", "noun", "verb", "adjective"], default="all",
                            help="Part of speech filter")
        parser.add_argument("-t", "--threads", type=int, default=4,
                            help="Number of threads to use")
        parser.add_argument("-o", "--output-dir", help="Output directory")
        
        args = parser.parse_args()
    
    start_time = time.time()
    
    try:
        downloader = DefinitionDownloader(
            args.language,
            args.output_dir if hasattr(args, 'output_dir') else None
        )
        
        definitions_file, not_found_file = downloader.download_definitions(
            args.word_file,
            args.pos,
            args.threads
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Downloading completed in {elapsed_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1
        
    return 0


if __name__ == "__main__":
    main() 