# 🎮 Wordle Clone - Color-Blind Accessible Web Application

A feature-rich Wordle clone with dual game modes, comprehensive statistics, and color-blind accessibility features. Built with Flask, Alpine.js, and PostgreSQL.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Flask](https://img.shields.io/badge/flask-2.3+-red.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

## ✨ Features

### 🎯 Core Game Features
- **Classic Wordle Mode**: Traditional 5-letter word game with 2,300+ words
- **Disney Mode**: Family-friendly Disney-themed words and characters
- **Daily Puzzles**: New puzzle every day with global synchronization
- **6 Guess Limit**: Classic Wordle gameplay mechanics
- **Real-time Feedback**: Instant color-coded letter feedback

### ♿ Accessibility Features
- **Color-Blind Friendly**: Blue/orange color scheme instead of red/green
- **Pattern Overlays**: Diagonal patterns for additional visual distinction
- **High Contrast**: 3px borders and enhanced visual clarity
- **Keyboard Navigation**: Full keyboard accessibility support
- **Screen Reader Support**: Semantic HTML and ARIA labels

### 🔐 User Management
- **JWT Authentication**: Secure token-based authentication
- **User Registration**: Email and username validation
- **Password Security**: bcrypt hashing with complexity requirements
- **Session Management**: Cross-device game state persistence

### 📊 Statistics & Analytics
- **Personal Stats**: Win percentage, streaks, guess distribution
- **Global Leaderboards**: Compete with other players
- **Game History**: Detailed past game reviews
- **Performance Metrics**: Average guesses and improvement tracking

### 🚀 Technical Features
- **Responsive Design**: Mobile-first responsive interface
- **Progressive Enhancement**: Works without JavaScript
- **Performance Optimized**: Database indexing and caching
- **Security Headers**: Production-ready security configuration
- **Rate Limiting**: Protection against abuse

## 🖥️ Screenshots

### Game Interface
```
┌─────────────────────────────────────┐
│  W O R D L E   C L O N E            │
├─────────────────────────────────────┤
│                                     │
│  🟦 🟧 ⬜ ⬜ ⬜  (Row 1)           │
│  ⬜ ⬜ ⬜ ⬜ ⬜  (Row 2)           │
│  ⬜ ⬜ ⬜ ⬜ ⬜  (Row 3)           │
│  ⬜ ⬜ ⬜ ⬜ ⬜  (Row 4)           │
│  ⬜ ⬜ ⬜ ⬜ ⬜  (Row 5)           │
│  ⬜ ⬜ ⬜ ⬜ ⬜  (Row 6)           │
│                                     │
│  Q W E R T Y U I O P                │
│   A S D F G H J K L                 │
│    Z X C V B N M                    │
│                                     │
└─────────────────────────────────────┘
```

🟦 = Correct letter and position (blue with diagonal pattern)
🟧 = Correct letter, wrong position (orange with reverse pattern)  
⬜ = Letter not in word (gray)

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd wordle-clone
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Initialize database**
   ```bash
   python scripts/setup_database.py
   python scripts/seed_words.py --modes all
   ```

6. **Run the application**
   ```bash
   python application.py --host=127.0.0.1 --port=8000
   ```

7. **Access the application**
   - Open your browser to `http://127.0.0.1:8000`
   - Register a new account or sign in
   - Start playing!

## 📁 Project Structure

```
wordle-clone/
├── src/app/                    # Application source code
│   ├── api/                    # API blueprints
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── game.py            # Game logic endpoints
│   │   ├── stats.py           # Statistics endpoints
│   │   └── health.py          # Health check endpoints
│   ├── models/                 # Database models
│   │   ├── user.py            # User model
│   │   └── game.py            # Game-related models
│   ├── services/               # Business logic layer
│   │   ├── auth_service.py    # Authentication service
│   │   ├── game_service.py    # Game orchestration
│   │   └── stats_service.py   # Statistics calculations
│   ├── repositories/           # Data access layer
│   ├── templates/              # Jinja2 templates
│   │   ├── auth/              # Authentication pages
│   │   ├── game/              # Game interface
│   │   └── components/        # Reusable components
│   ├── middleware/             # Security and performance
│   ├── utils/                  # Utility functions
│   └── database/               # Database configuration
├── scripts/                    # Management scripts
│   ├── seed_words.py          # Word list seeding
│   ├── setup_database.py      # Database optimization
│   └── production_setup.py    # Production deployment
├── docs/                       # Documentation
├── migrations/                 # Database migrations
└── requirements.txt            # Python dependencies
```

## 🎮 How to Play

### Classic Mode
1. **Objective**: Guess the 5-letter word in 6 attempts or fewer
2. **Feedback**: 
   - 🟦 Blue with pattern = Correct letter in correct position
   - 🟧 Orange with pattern = Correct letter in wrong position
   - ⬜ Gray = Letter not in the word
3. **Strategy**: Use common letters and vowels in your first guesses

### Disney Mode
1. **Same rules** as Classic mode
2. **Disney words**: Characters, movies, locations, and Disney universe terms
3. **Family-friendly**: Curated word list appropriate for all ages

## 🔧 API Documentation

### Authentication Endpoints
```
POST /api/auth/register    # User registration
POST /api/auth/login       # User login
POST /api/auth/refresh     # Token refresh
GET  /api/auth/me          # Current user info
```

### Game Endpoints
```
GET  /api/game/daily/{mode}        # Get today's puzzle
POST /api/game/guess               # Submit a guess
GET  /api/game/session/{id}        # Get game session
POST /api/game/validate            # Validate word
GET  /api/game/history/{mode}      # Game history
GET  /api/game/modes               # Available modes
```

### Statistics Endpoints
```
GET  /api/stats/me                 # User statistics
GET  /api/stats/leaderboard/{mode} # Global leaderboard
GET  /api/stats/rank/{mode}        # User ranking
GET  /api/stats/global/{mode}      # Global statistics
```

### Response Format
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt with 12+ rounds
- **Rate Limiting**: Protection against abuse
- **Input Validation**: Comprehensive data validation
- **Security Headers**: OWASP recommended headers
- **CORS Protection**: Configured for frontend domains
- **SQL Injection Prevention**: Parameterized queries

## 📊 Database Schema

### Core Tables
- **users**: User accounts and authentication
- **daily_words**: Daily puzzle words for each mode
- **word_list**: Valid words and answers by game mode
- **game_sessions**: Individual game state and history
- **user_stats**: User statistics and leaderboard data

### Key Relationships
- Users have multiple game sessions
- Each game session belongs to a daily word
- User stats are calculated per game mode
- Word lists are segregated by game mode

## 🚀 Production Deployment

### Docker Deployment (Recommended)
```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment
1. **Set up production environment**
   ```bash
   python scripts/production_setup.py
   ```

2. **Install production dependencies**
   ```bash
   pip install -r requirements.prod.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.production .env
   # Update with production values
   ```

4. **Run with Gunicorn**
   ```bash
   gunicorn --bind 0.0.0.0:8000 --workers 4 application:app
   ```

### Production Checklist
- [ ] Update secret keys and passwords
- [ ] Configure SSL certificates
- [ ] Set up Redis for caching and rate limiting
- [ ] Configure PostgreSQL with backups
- [ ] Set up monitoring and logging
- [ ] Configure firewall rules
- [ ] Test health check endpoint (`/api/health`)

## 🧪 Testing

### Manual Testing
```bash
# Test API endpoints
curl http://127.0.0.1:8000/api/health

# Test authentication
curl -X POST http://127.0.0.1:8000/api/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{"username":"test","email":"test@example.com","password":"Test123!"}'
```

### Automated Testing
```bash
# Run test suite (when implemented)
python -m pytest tests/
```

## 📈 Performance Optimization

### Database Optimizations
- **Indexes**: Strategic indexing on frequently queried columns
- **Connection Pooling**: Efficient database connection management
- **Query Optimization**: Optimized queries with proper joins
- **Views**: Database views for complex repeated queries

### Caching Strategy
- **Daily Puzzles**: Cached until end of day
- **User Statistics**: 10-minute cache with invalidation
- **Leaderboards**: 5-minute cache for frequently accessed data
- **Word Validation**: 24-hour cache for word lookup results

### Frontend Performance
- **CDN Assets**: Tailwind CSS and Alpine.js via CDN
- **Minimal JavaScript**: Progressive enhancement approach
- **Responsive Images**: Optimized for different screen sizes
- **Gzip Compression**: Enabled for text assets

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Kill process on port 5000
   lsof -ti:5000 | xargs kill -9
   
   # Use different port
   python application.py --port=8000
   ```

2. **Database connection errors**
   ```bash
   # Check PostgreSQL is running
   pg_ctl status
   
   # Verify connection string in .env
   DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
   ```

3. **Missing word lists**
   ```bash
   # Reseed word lists
   python scripts/seed_words.py --modes all --clear
   ```

### Logging
- Application logs: Console output in development
- Error tracking: Sentry integration available
- Access logs: Nginx logs in production
- Database logs: PostgreSQL query logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Original Wordle**: Inspired by Josh Wardle's Wordle
- **Color Accessibility**: Following WCAG guidelines for color-blind users
- **Disney Words**: Curated family-friendly Disney universe terms
- **Flask Community**: For excellent documentation and examples

## 📞 Support

- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join community discussions
- **Documentation**: Comprehensive docs in `/docs` folder
- **Health Check**: Monitor application at `/api/health`

---

**🎉 Ready to play? Visit http://127.0.0.1:8000 and start your Wordle journey!**