#!/usr/bin/env python3
"""
Advanced word list seeding script for Wordle application.
Provides comprehensive word list management with validation and reporting.
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple
import logging

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from app import create_app
from app.models.game import WordList, GameMode
from app.database import db


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WordListSeeder:
    """Advanced word list seeding with validation and reporting."""
    
    def __init__(self):
        """Initialize the word list seeder."""
        self.app = create_app()
        self.stats = {
            'classic': {'added': 0, 'skipped': 0, 'errors': 0},
            'disney': {'added': 0, 'skipped': 0, 'errors': 0}
        }
        self.validation_errors = []
    
    def validate_word(self, word: str) -> Tuple[bool, str]:
        """Validate a word meets requirements."""
        if not word:
            return False, "Empty word"
        
        if len(word) != 5:
            return False, f"Word must be 5 letters, got {len(word)}"
        
        if not word.isalpha():
            return False, "Word must contain only letters"
        
        if not word.isupper():
            return False, "Word must be uppercase"
        
        return True, ""
    
    def load_word_lists(self) -> Dict[str, Dict[str, List[str]]]:
        """Load word lists from files or return defaults."""
        # Default word lists (curated for the game)
        classic_answers = [
            "ABOUT", "ABOVE", "ABUSE", "ACTOR", "ACUTE", "ADMIT", "ADOPT", "ADULT", "AFTER", "AGAIN",
            "AGENT", "AGREE", "AHEAD", "ALARM", "ALBUM", "ALERT", "ALIEN", "ALIGN", "ALIKE", "ALIVE",
            "ALLOW", "ALONE", "ALONG", "ALTER", "ANGEL", "ANGER", "ANGLE", "ANGRY", "APART", "APPLE",
            "APPLY", "ARENA", "ARGUE", "ARISE", "ARRAY", "ASIDE", "ASSET", "AUDIO", "AUDIT", "AVOID",
            "AWAKE", "AWARD", "AWARE", "BADLY", "BAKER", "BASES", "BASIC", "BEACH", "BEGAN", "BEGIN",
            "BEING", "BELOW", "BENCH", "BIRTH", "BLACK", "BLAME", "BLANK", "BLAST", "BLIND", "BLOCK",
            "BLOOD", "BOARD", "BOAST", "BOATS", "BONDS", "BONUS", "BOOST", "BOOTH", "BOUND", "BRAIN",
            "BRAND", "BRASS", "BRAVE", "BREAD", "BREAK", "BREED", "BRIEF", "BRING", "BROAD", "BROKE",
            "BROWN", "BUILD", "BUILT", "BUYER", "CABLE", "CARRY", "CATCH", "CAUSE", "CHAIN", "CHAIR",
            "CHAOS", "CHARM", "CHART", "CHASE", "CHEAP", "CHECK", "CHEST", "CHIEF", "CHILD", "CHINA",
            "CHOSE", "CIVIL", "CLAIM", "CLASS", "CLEAN", "CLEAR", "CLICK", "CLIMB", "CLOCK", "CLOSE",
            "CLOUD", "COACH", "COAST", "COULD", "COUNT", "COURT", "COVER", "CRAFT", "CRASH", "CRAZY",
            "CREAM", "CRIME", "CROSS", "CROWD", "CROWN", "CRUDE", "CURVE", "CYCLE", "DAILY", "DANCE",
            "DATED", "DEALT", "DEATH", "DEBUT", "DELAY", "DEPTH", "DOING", "DOUBT", "DOZEN", "DRAFT",
            "DRAMA", "DRANK", "DRAWN", "DREAM", "DRESS", "DRILL", "DRINK", "DRIVE", "DROVE", "DYING",
            "EAGER", "EARLY", "EARTH", "EIGHT", "ELITE", "EMPTY", "ENEMY", "ENJOY", "ENTER", "ENTRY",
            "EQUAL", "ERROR", "EVENT", "EVERY", "EXACT", "EXIST", "EXTRA", "FAITH", "FALSE", "FAULT",
            "FIBER", "FIELD", "FIFTH", "FIFTY", "FIGHT", "FINAL", "FIRST", "FIXED", "FLASH", "FLEET",
            "FLOOR", "FLUID", "FOCUS", "FORCE", "FORTH", "FORTY", "FORUM", "FOUND", "FRAME", "FRANK",
            "FRAUD", "FRESH", "FRONT", "FROST", "FRUIT", "FULLY", "FUNNY", "GIANT", "GIVEN", "GLASS",
            "GLOBE", "GOING", "GRACE", "GRADE", "GRAND", "GRANT", "GRASS", "GRAVE", "GREAT", "GREEN",
            "GROSS", "GROUP", "GROWN", "GUARD", "GUESS", "GUEST", "GUIDE", "HAPPY", "HEART", "HEAVY",
            "HENCE", "HORSE", "HOTEL", "HOUSE", "HUMAN", "IDEAL", "IMAGE", "INDEX", "INNER", "INPUT",
            "ISSUE", "JAPAN", "JIMMY", "JOINT", "JONES", "JUDGE", "KNOWN", "LABEL", "LARGE", "LASER",
            "LATER", "LAUGH", "LAYER", "LEARN", "LEASE", "LEAST", "LEAVE", "LEGAL", "LEVEL", "LEWIS",
            "LIGHT", "LIMIT", "LINKS", "LIVES", "LOCAL", "LOOSE", "LOWER", "LUCKY", "LUNCH", "LYING",
            "MAGIC", "MAJOR", "MAKER", "MARCH", "MARIA", "MATCH", "MAYBE", "MAYOR", "MEANT", "MEDIA",
            "METAL", "MIGHT", "MINOR", "MINUS", "MIXED", "MODEL", "MONEY", "MONTH", "MORAL", "MOTOR",
            "MOUNT", "MOUSE", "MOUTH", "MOVED", "MOVIE", "MUSIC", "NEEDS", "NEVER", "NEWLY", "NIGHT",
            "NOISE", "NORTH", "NOTED", "NOVEL", "NURSE", "OCCUR", "OCEAN", "OFFER", "OFTEN", "ORDER",
            "OTHER", "OUGHT", "PAINT", "PANEL", "PAPER", "PARTY", "PEACE", "PETER", "PHASE", "PHONE",
            "PHOTO", "PIANO", "PIECE", "PILOT", "PITCH", "PLACE", "PLAIN", "PLANE", "PLANT", "PLATE",
            "POINT", "POUND", "POWER", "PRESS", "PRICE", "PRIDE", "PRIME", "PRINT", "PRIOR", "PRIZE",
            "PROOF", "PROUD", "PROVE", "QUEEN", "QUICK", "QUIET", "QUITE", "RADIO", "RAISE", "RANGE",
            "RAPID", "RATIO", "REACH", "READY", "REALM", "REBEL", "REFER", "RELAX", "REPAY", "REPLY",
            "RIGHT", "RIGID", "RIVAL", "RIVER", "ROBIN", "ROGER", "ROMAN", "ROUGH", "ROUND", "ROUTE",
            "ROYAL", "RURAL", "SCALE", "SCENE", "SCOPE", "SCORE", "SENSE", "SERVE", "SETUP", "SEVEN",
            "SHALL", "SHAPE", "SHARE", "SHARP", "SHEET", "SHELF", "SHELL", "SHIFT", "SHINE", "SHIRT",
            "SHOCK", "SHOOT", "SHORT", "SHOWN", "SIGHT", "SIMON", "SIXTH", "SIXTY", "SIZED", "SKILL",
            "SLEEP", "SLIDE", "SMALL", "SMART", "SMILE", "SMITH", "SMOKE", "SOLID", "SOLVE", "SORRY",
            "SOUND", "SOUTH", "SPACE", "SPARE", "SPEAK", "SPEED", "SPEND", "SPENT", "SPLIT", "SPOKE",
            "SPORT", "STAFF", "STAGE", "STAKE", "STAND", "START", "STATE", "STEAM", "STEEL", "STEEP",
            "STEER", "STEVE", "STICK", "STILL", "STOCK", "STONE", "STOOD", "STORE", "STORM", "STORY",
            "STRIP", "STUCK", "STUDY", "STUFF", "STYLE", "SUGAR", "SUITE", "SUPER", "SWEET", "TABLE",
            "TAKEN", "TASTE", "TAXES", "TEACH", "TEENS", "TEETH", "TERRY", "TEXAS", "THANK", "THEFT",
            "THEIR", "THEME", "THERE", "THESE", "THICK", "THING", "THINK", "THIRD", "THOSE", "THREE",
            "THREW", "THROW", "THUMB", "TIGER", "TIGHT", "TIRED", "TITLE", "TODAY", "TOPIC", "TOTAL",
            "TOUCH", "TOUGH", "TOWER", "TRACK", "TRADE", "TRAIN", "TREAT", "TREND", "TRIAL", "TRIBE",
            "TRICK", "TRIED", "TRIES", "TRUCK", "TRULY", "TRUNK", "TRUST", "TRUTH", "TWICE", "UNCLE",
            "UNDUE", "UNION", "UNITY", "UNTIL", "UPPER", "UPSET", "URBAN", "USAGE", "USUAL", "VALID",
            "VALUE", "VIDEO", "VIRUS", "VISIT", "VITAL", "VOCAL", "VOICE", "WASTE", "WATCH", "WATER",
            "WAVES", "WEIRD", "WHEEL", "WHERE", "WHICH", "WHILE", "WHITE", "WHOLE", "WHOSE", "WOMAN",
            "WOMEN", "WORLD", "WORRY", "WORSE", "WORST", "WORTH", "WOULD", "WRITE", "WRONG", "WROTE",
            "YOUNG", "YOUTH"
        ]
        
        classic_guesses = [
            "AAHED", "AALII", "AARGH", "ABACA", "ABACI", "ABACS", "ABAFT", "ABAKA", "ABAMP", "ABAND",
            "ABASH", "ABASK", "ABATE", "ABAYA", "ABBAS", "ABBED", "ABBES", "ABBEY", "ABBOT", "ABCEE",
            "ABEAM", "ABEAR", "ABELE", "ABERS", "ABETS", "ABHOR", "ABIDE", "ABLED", "ABLER", "ABLES",
            "ABLET", "ABLOW", "ABMHO", "ABODE", "ABOHM", "ABOIL", "ABOMA", "ABOON", "ABORD", "ABORE",
            "ABORT", "ABOTT", "ABOUL", "ABRAY", "ABRED", "ABRIM", "ABRIN", "ABRIS", "ABSEY", "ABSIT",
            "ABUNA", "ABUNE", "ABUTS", "ABUZZ", "ABYES", "ABYSM", "ABYSS", "ACAIS", "ACARI", "ACEDY",
            "ACERS", "ACHES", "ACHEY", "ACIDS", "ACIDY", "ACING", "ACINI", "ACKEE", "ACKER", "ACMES",
            "ACMIC", "ACNED", "ACNES", "ACOCK", "ACOLD", "ACORN", "ACRED", "ACRES", "ACRID", "ACROS",
            "ACTED", "ACTIN", "ACTON", "ACUAN", "ACYLS", "ADAGE", "ADAPT", "ADDAX", "ADDED", "ADDER",
            "ADDIO", "ADDLE", "ADEEM", "ADEPT", "ADHAN", "ADIEU", "ADIOS", "ADITS", "ADMAN", "ADMIN"
        ]
        
        disney_answers = [
            "ARIEL", "BELLE", "BEAST", "SIMBA", "WOODY", "BUZZY", "GENIE", "STICH", "PUMBA", "TIMON", 
            "GOOFY", "PLUTO", "BAMBI", "DUMBO", "ALICE", "QUEEN", "MARCH", "WHITE", "HEART", "SPADE", 
            "MAGIC", "SPELL", "FAIRY", "DREAM", "BRAVE", "MOANA", "OCEAN", "BEACH", "SHELL", "PEARL", 
            "CORAL", "SHARK", "WHALE", "SWORD", "CROWN", "TOWER", "LIGHT", "WATER", "EARTH", "GHOST", 
            "DEMON", "ANGEL", "DEVIL", "SAINT", "ROYAL", "THROW", "APPLE", "GRAPE", "LEMON", "PEACH", 
            "MANGO", "SWEET", "FRESH", "YOUNG", "SMALL", "LARGE", "THICK", "QUICK", "QUIET", "CLEAN", 
            "SHARP", "SMILE", "HAPPY", "LUCKY", "HONOR", "TRUST", "PEACE", "DANCE", "MUSIC", "LAUGH", 
            "CHARM", "GRACE", "POWER", "FROST", "FLAME", "STONE", "JEWEL"
        ]
        
        disney_guesses = [
            "AGRAB", "COCO", "FLYNN", "HANS", "JAFAR", "MULAN", "RALPH", "TIANA", "WENDY", "ZAZU",
            "BAYOU", "CHILD", "EMOJI", "JOKER", "KNIFE", "MERCY", "NOBLE", "OASIS", "PARTY", "RIDER",
            "TITAN", "ULTRA", "VIGOR", "WITCH", "YACHT", "ARMOR", "BLAZE", "CLOUD", "EAGLE", "GIANT",
            "HAVEN", "IVORY", "JOUST", "KNAVE", "LANCE", "MANOR", "NORTH", "OPTIC", "PATCH", "QUAKE",
            "REALM", "STORM", "TOOTH", "UNITE", "VENOM", "WHEAT", "XERUS"
        ]
        
        return {
            'classic': {
                'answers': classic_answers,
                'guesses': classic_guesses
            },
            'disney': {
                'answers': disney_answers,
                'guesses': disney_guesses
            }
        }
    
    def add_word_to_db(self, word: str, game_mode: GameMode, is_answer: bool, frequency_rank: int) -> bool:
        """Add a single word to the database."""
        try:
            is_valid, error_msg = self.validate_word(word)
            if not is_valid:
                self.validation_errors.append(f"{word}: {error_msg}")
                return False
            
            # Check if word already exists
            existing = db.session.query(WordList).filter_by(
                word=word,
                game_mode=game_mode
            ).first()
            
            if existing:
                logger.debug(f"Word {word} already exists in {game_mode.value} mode")
                return False
            
            # Create new word entry
            word_entry = WordList(
                word=word,
                game_mode=game_mode,
                is_answer=is_answer,
                frequency_rank=frequency_rank
            )
            
            db.session.add(word_entry)
            return True
            
        except Exception as e:
            logger.error(f"Error adding word {word}: {e}")
            return False
    
    def seed_word_list(self, game_mode: str, clear_existing: bool = False) -> Dict[str, int]:
        """Seed words for a specific game mode."""
        mode_enum = GameMode.CLASSIC if game_mode == 'classic' else GameMode.DISNEY
        stats = {'added': 0, 'skipped': 0, 'errors': 0}
        
        with self.app.app_context():
            if clear_existing:
                logger.info(f"Clearing existing {game_mode} words...")
                deleted = db.session.query(WordList).filter_by(game_mode=mode_enum).delete()
                logger.info(f"Deleted {deleted} existing words")
            
            # Load word lists
            word_lists = self.load_word_lists()
            mode_words = word_lists[game_mode]
            
            # Add answer words
            logger.info(f"Adding {game_mode} answer words...")
            frequency_rank = 1
            
            for word in mode_words['answers']:
                if self.add_word_to_db(word, mode_enum, True, frequency_rank):
                    stats['added'] += 1
                    frequency_rank += 1
                else:
                    stats['skipped'] += 1
            
            # Add guess words
            logger.info(f"Adding {game_mode} guess words...")
            
            for word in mode_words['guesses']:
                if self.add_word_to_db(word, mode_enum, False, frequency_rank):
                    stats['added'] += 1
                    frequency_rank += 1
                else:
                    stats['skipped'] += 1
            
            try:
                db.session.commit()
                logger.info(f"Successfully committed {stats['added']} words for {game_mode} mode")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to commit words for {game_mode}: {e}")
                stats['errors'] = stats['added']
                stats['added'] = 0
        
        return stats
    
    def generate_report(self) -> str:
        """Generate a detailed seeding report."""
        with self.app.app_context():
            # Get current word counts
            classic_count = db.session.query(WordList).filter_by(game_mode=GameMode.CLASSIC).count()
            disney_count = db.session.query(WordList).filter_by(game_mode=GameMode.DISNEY).count()
            
            classic_answers = db.session.query(WordList).filter_by(
                game_mode=GameMode.CLASSIC, is_answer=True
            ).count()
            disney_answers = db.session.query(WordList).filter_by(
                game_mode=GameMode.DISNEY, is_answer=True
            ).count()
            
            report = f"""
📊 WORD LIST SEEDING REPORT
{'=' * 50}

📝 Classic Mode:
   Total Words: {classic_count}
   Answer Words: {classic_answers}
   Guess Words: {classic_count - classic_answers}
   Added: {self.stats['classic']['added']}
   Skipped: {self.stats['classic']['skipped']}
   Errors: {self.stats['classic']['errors']}

🏰 Disney Mode:
   Total Words: {disney_count}
   Answer Words: {disney_answers}
   Guess Words: {disney_count - disney_answers}
   Added: {self.stats['disney']['added']}
   Skipped: {self.stats['disney']['skipped']}
   Errors: {self.stats['disney']['errors']}

🎯 Summary:
   Total Words in Database: {classic_count + disney_count}
   Total Added This Session: {self.stats['classic']['added'] + self.stats['disney']['added']}
   Total Skipped: {self.stats['classic']['skipped'] + self.stats['disney']['skipped']}

"""
            
            if self.validation_errors:
                report += f"""
⚠️ Validation Errors ({len(self.validation_errors)}):
{chr(10).join(f"   - {error}" for error in self.validation_errors[:10])}
"""
                if len(self.validation_errors) > 10:
                    report += f"   ... and {len(self.validation_errors) - 10} more\n"
        
        return report
    
    def run(self, modes: List[str], clear_existing: bool = False) -> None:
        """Run the word list seeding process."""
        logger.info("🚀 Starting word list seeding...")
        
        for mode in modes:
            logger.info(f"Processing {mode} mode...")
            self.stats[mode] = self.seed_word_list(mode, clear_existing)
        
        # Generate and display report
        report = self.generate_report()
        print(report)
        
        logger.info("✅ Word list seeding completed!")


def main():
    """Main entry point for the seeding script."""
    parser = argparse.ArgumentParser(description='Seed word lists for Wordle application')
    parser.add_argument(
        '--modes', 
        nargs='+', 
        choices=['classic', 'disney', 'all'], 
        default=['all'],
        help='Game modes to seed (default: all)'
    )
    parser.add_argument(
        '--clear', 
        action='store_true',
        help='Clear existing words before seeding'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine modes to process
    if 'all' in args.modes:
        modes = ['classic', 'disney']
    else:
        modes = args.modes
    
    # Run seeding
    seeder = WordListSeeder()
    seeder.run(modes, args.clear)


if __name__ == "__main__":
    main()