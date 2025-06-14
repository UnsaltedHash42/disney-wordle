# Wordle Web App - Design Document

## Project Overview

A web-based Wordle clone featuring user authentication, comprehensive statistics tracking, global leaderboards, and dual game modes (Classic and Disney). The application follows Python best practices with Flask as the web framework, PostgreSQL for data persistence, and a clean separation of concerns through service layer architecture.

## Tech Stack

**Backend:** Python 3.10+ with Flask
- Flask application factory pattern
- SQLAlchemy 2.0+ with repository pattern
- Flask-JWT-Extended for authentication
- Pydantic for configuration and validation
- No async/await usage - pure synchronous Flask

**Frontend:** Flask Templates + Alpine.js
- Server-side rendering with Jinja2 templates
- Alpine.js for reactive UI components
- Tailwind CSS for styling
- Progressive enhancement philosophy

**Database:** PostgreSQL with SQLAlchemy
- Connection pooling with QueuePool
- Flask-Migrate for schema management
- JSON fields for flexible data storage

**Development:** 
- Virtual environment with venv (create first)
- Docker Compose for development environment
- Requirements.txt for dependency management

## Architecture

### Application Structure
```
src/app/
├── __init__.py          # App factory
├── models/              # SQLAlchemy models with mixins
├── api/                 # Flask blueprints (auth, game, stats)
├── services/            # Business logic layer
├── repositories/        # Data access layer
├── utils/               # Decorators, validators, helpers
├── config/              # Pydantic settings
└── templates/           # Jinja2 templates with Alpine.js
```

### Design Patterns
- **Application Factory:** Environment-specific Flask app creation
- **Repository Pattern:** Data access abstraction
- **Service Layer:** Business logic separation from HTTP concerns
- **Blueprint Organization:** Feature-based route grouping
- **Mixin Pattern:** Reusable model functionality (timestamps, soft delete)

## Core Features

### Authentication System
- JWT-based authentication with 15-minute access tokens
- User registration with email/username validation
- Password hashing with bcrypt (12+ rounds)
- Rate limiting on auth endpoints (5 registration attempts/minute)
- Email verification workflow

### Game Mechanics
- **Daily Puzzle System:** One puzzle per day per mode (UTC-based)
- **Dual Game Modes:** Classic Wordle (~2,300 words) and Disney Wordle (~800 words)
- **Guess Processing:** 6 attempts with real-time color-coded feedback
- **Word Validation:** Server-side validation against approved word lists
- **Game State Persistence:** Session recovery across browser refreshes

### Statistics & Leaderboards
- **Personal Stats:** Games played/won, streaks, guess distribution, win percentage
- **Global Leaderboards:** Win percentage, current streak, total wins (per mode)
- **Game History:** Historical performance tracking with date/result storage

## Database Design

### Core Models

**User Model:**
```python
class User(BaseModel):
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)  
    password_hash = db.Column(db.String(255), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
```

**Game Session Model:**
```python
class GameSession(BaseModel):
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    daily_word_id = db.Column(db.Integer, db.ForeignKey('daily_words.id'))
    guesses = db.Column(db.JSON, default=list)  # [{word: "HELLO", feedback: ["correct", "absent", ...]}]
    completed = db.Column(db.Boolean, default=False)
    won = db.Column(db.Boolean, default=False)
    attempts_used = db.Column(db.Integer, default=0)
```

**Daily Word Model:**
```python
class DailyWord(BaseModel):
    word = db.Column(db.String(5), nullable=False)
    game_mode = db.Column(db.Enum(GameMode), nullable=False)  # 'classic' or 'disney'
    date = db.Column(db.Date, nullable=False)
    # Unique constraint on (date, game_mode)
```

**User Statistics Model:**
```python
class UserStats(BaseModel):
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    game_mode = db.Column(db.Enum(GameMode), nullable=False)
    games_played = db.Column(db.Integer, default=0)
    games_won = db.Column(db.Integer, default=0)
    current_streak = db.Column(db.Integer, default=0)
    max_streak = db.Column(db.Integer, default=0)
    guess_distribution = db.Column(db.JSON, default={"1":0,"2":0,"3":0,"4":0,"5":0,"6":0})
```

**Word List Model:**
```python
class WordList(BaseModel):
    word = db.Column(db.String(5), nullable=False)
    game_mode = db.Column(db.Enum(GameMode), nullable=False)
    is_answer = db.Column(db.Boolean, default=True)  # False for valid guesses only
    frequency_rank = db.Column(db.Integer)
```

### Key Relationships
- User → UserStats (one-to-many, per game mode)
- User → GameSession (one-to-many)
- DailyWord → GameSession (one-to-many)
- Unique constraints: (user_id, daily_word_id) for GameSession

## API Design

### Authentication Endpoints
```
POST /api/auth/register    # User registration
POST /api/auth/login      # User login  
POST /api/auth/refresh    # Token refresh
GET  /api/auth/me         # Current user info
```

### Game Endpoints
```
GET  /api/game/daily/{mode}        # Get today's puzzle info
POST /api/game/guess               # Submit guess
GET  /api/game/session/{date}/{mode}  # Get specific game session
POST /api/game/validate/{word}     # Validate word exists
```

### Statistics Endpoints
```
GET  /api/stats/user/{user_id}     # User stats for both modes
GET  /api/stats/leaderboard/{mode} # Global leaderboard
GET  /api/stats/history/{user_id}  # Game history
```

### Response Format
```json
{
  "success": true,
  "data": {...},
  "error": null
}
```

## Word Lists Implementation

### Classic Wordle Words
- **Answer Words:** 2,315 five-letter words (curated for appropriate difficulty)
- **Valid Guesses:** ~12,000 additional valid English words
- **Source Strategy:** Use established Wordle word lists or equivalent curated sets
- **Storage:** Database with frequency rankings for balanced selection

### Disney Word Set
**Target:** 800+ Disney-themed five-letter words

**Categories:**
1. **Characters (200+ words):** ARIEL, BELLE, BEAST, SIMBA, WOODY, BUZZ, ELSA, ANNA, OLAF, DORY, GENIE, STICH, PUMBA, TIMON
2. **Movies/Themes (150+ words):** BRAVE, COCO, MAGIC, OCEAN, FROST, LIGHT, HEART, DREAM, ROYAL, FAIRY
3. **Locations (100+ words):** AGRAB (Agrabah), PRIDE (Pride Rock), TOWER, BAYOU, NEVER (Neverland), ATLAS (Atlantis)
4. **Objects (200+ words):** SWORD, CROWN, APPLE, GLASS, WAND, SPELL, POTION, PEARL, SHELL, SCALE, FLAME, STONE, JEWEL
5. **Concepts (150+ words):** HAPPY, LUCKY, BRAVE, SWEET, PURE, TRUST, SMILE, SHINE, DANCE, DREAM, WISH

**Implementation Strategy:**
- Start with high-confidence Disney words
- Expand with fairy tale and fantasy terms
- Community suggestion system for growth
- Regular curation for appropriateness

## Frontend Architecture

### Template Structure
```
templates/
├── base.html              # Base template with Alpine.js
├── auth/
│   ├── login.html
│   └── register.html
├── game/
│   ├── play.html          # Main game interface
│   └── stats.html         # Statistics display
└── components/
    ├── navbar.html
    ├── game-board.html     # 6x5 grid component
    └── keyboard.html       # Virtual keyboard
```

### Alpine.js Components
**Game Controller:**
```javascript
Alpine.data('gameController', () => ({
    gameMode: 'classic',
    gameBoard: Array(6).fill().map(() => Array(5).fill({letter: '', status: ''})),
    currentGuess: '',
    gameCompleted: false,
    gameWon: false,
    sessionId: null,
    
    async submitGuess() { /* API call to /api/game/guess */ },
    handleKeyPress(key) { /* Keyboard handling */ },
    switchMode(mode) { /* Mode switching */ }
}))
```

**Stats Display:**
```javascript
Alpine.data('statsController', () => ({
    userStats: {},
    gameHistory: [],
    leaderboard: [],
    
    async loadStats() { /* API call to /api/stats/user */ },
    async loadLeaderboard() { /* API call to /api/stats/leaderboard */ }
}))
```

### Styling Strategy
- Tailwind CSS via CDN for rapid development
- Custom CSS for game-specific animations
- Responsive design with mobile-first approach
- Dark mode support with Alpine.js persistence

## Service Layer Design

### Authentication Service
```python
class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()
    
    def register_user(self, data: dict) -> User:
        # Validation, duplicate checking, password hashing
        
    def authenticate_user(self, email: str, password: str) -> User:
        # Credential verification, account status checking
```

### Game Service  
```python
class GameService:
    def __init__(self):
        self.game_repo = GameRepository()
        self.word_validator = WordValidator()
        
    def get_daily_puzzle(self, user_id: int, game_mode: str) -> dict:
        # Get/create daily word, get/create user session
        
    def process_guess(self, user_id: int, data: dict) -> dict:
        # Validate guess, generate feedback, update session, calculate stats
```

### Statistics Service
```python
class StatsService:
    def __init__(self):
        self.stats_repo = StatsRepository()
        
    def update_user_stats(self, user_id: int, game_result: dict):
        # Update games played/won, streaks, guess distribution
        
    def get_leaderboard(self, game_mode: str, metric: str) -> list:
        # Calculate and return ranked users
```

## Security Implementation

### Authentication Security
- JWT tokens with short expiration (15 minutes)
- Refresh token rotation for session extension  
- Rate limiting on authentication endpoints
- Password complexity requirements
- Account lockout after failed attempts

### Application Security
- Input validation with Pydantic schemas
- SQL injection prevention via SQLAlchemy
- XSS protection with template escaping
- CORS configuration for API access
- CSRF protection for state changes

### Data Protection
- Password hashing with bcrypt
- Environment variables for secrets
- Database connection encryption
- Audit logging for sensitive operations

## Performance Considerations

### Database Optimization
- Strategic indexing on frequently queried columns
- Connection pooling for concurrent requests
- Query optimization with proper joins
- Prepared statements for repeated queries

### Caching Strategy
- Daily word caching to reduce database hits
- Leaderboard caching with periodic refresh
- User session caching for game state
- Static asset caching with appropriate headers

### Response Time Targets
- API endpoints: <200ms average
- Database queries: <50ms average  
- Page loads: <2 seconds initial
- Game interactions: <100ms response

## Development Workflow

### Implementation Phases

**Phase 1: Foundation**
- Virtual environment setup (venv)
- Flask application factory with configuration
- SQLAlchemy models with relationships
- Authentication system with JWT
- Basic API endpoints

**Phase 2: Core Game Logic**
- Daily puzzle system implementation
- Guess processing with feedback generation
- Game session management
- Word validation system
- Game API endpoints

**Phase 3: Frontend Interface**
- Flask templates with Alpine.js integration
- Game board and keyboard components
- Authentication forms
- Responsive design implementation
- API integration

**Phase 4: Statistics & Polish**
- Statistics calculation and display
- Leaderboard system implementation
- Performance optimization
- Production deployment configuration
- Comprehensive testing

### Quality Assurance
- Unit tests for services and utilities
- Integration tests for API endpoints
- Frontend testing for user interactions
- Database migration testing
- Performance benchmarking

### Documentation Maintenance
- Architectural decisions in notes.md
- API documentation with examples
- Database schema documentation
- Deployment and configuration guides

## Deployment Architecture

### Development Environment
- Docker Compose with hot reload
- Local PostgreSQL with test data
- Environment variable management
- Automatic database migrations

### Production Environment
- Containerized deployment with health checks
- Production PostgreSQL with backups
- SSL termination and security headers
- Monitoring and logging integration
- Automated deployment pipeline

## Success Criteria

### Technical Metrics
- Zero critical security vulnerabilities
- 99.9% uptime in production
- API response times within targets
- Comprehensive test coverage (>80%)
- Clean code following Python conventions

### User Experience
- Intuitive game interface
- Accurate statistics tracking
- Reliable daily puzzle availability
- Fast game interactions
- Cross-device compatibility

### Business Objectives
- User registration and retention
- Daily active user engagement
- High game completion rates
- Disney mode adoption
- Social sharing utilization

This design serves as the authoritative specification for the Wordle web application, providing clear architectural guidance while maintaining flexibility for implementation details within established patterns and conventions.