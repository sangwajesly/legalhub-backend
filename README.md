# LegalHub Backend

**LegalHub** is an innovative web-based legal assistance platform designed to bridge the gap between citizens and legal services through technology. By simplifying legal jargon and providing accessible legal resources, LegalHub empowers users to understand their rights, connect with legal professionals, and report cases with ease.

## 🌟 Overview

LegalHub is a comprehensive web application that democratizes access to legal information and services. The platform features a ChatGPT-style conversational interface powered by AI to make legal knowledge accessible to everyone, regardless of their legal background.

## 🎯 Key Features

### 1. **ChatGPT-Style Legal Chatbot**
- **Conversational AI Interface**: Full-featured chat experience similar to ChatGPT, designed specifically for legal queries
- **Natural Language Processing**: Understands and responds to legal questions in plain, everyday language
- **Multilingual Support**: Processes queries and generates responses in multiple languages
- **Context-Aware Conversations**: Maintains conversation history and context across multiple exchanges
- **Legal Jargon Translation**: Automatically converts complex legal terminology into simple, understandable language
- **Follow-up Questions**: Handles multi-turn conversations with contextual understanding
- **Citation & Sources**: Provides references to relevant laws, statutes, and legal precedents when applicable
- **Conversation History**: Saves and retrieves past conversations for users
- **Streaming Responses**: Real-time response generation for better user experience
- **24/7 Availability**: Always-on AI assistant for immediate legal guidance

**API Endpoints for Chat:**
- `POST /api/chat/message` - Send message and receive AI response
- `GET /api/chat/history` - Retrieve conversation history
- `POST /api/chat/session` - Create new chat session
- `DELETE /api/chat/session/:id` - Clear chat session
- `POST /api/chat/feedback` - Submit feedback on AI responses

### 2. **Lawyer Booking System**
- **Lawyer Directory API**: Search and filter lawyers by specialization, location, rating, and availability
- **Profile Management**: Comprehensive lawyer profile endpoints with credentials and reviews
- **Booking Management**: Handle consultation scheduling and calendar integration
- **Availability System**: Real-time availability checking and slot booking
- **Notification Service**: Automated booking confirmations and reminders
- **Payment Processing**: Secure payment gateway integration
- **Rating & Review System**: Collect and manage client feedback

**API Endpoints:**
- `GET /api/lawyers` - List lawyers with filters
- `GET /api/lawyers/:id` - Get lawyer profile
- `POST /api/bookings` - Create new booking
- `GET /api/bookings/:userId` - Get user bookings
- `PUT /api/bookings/:id` - Update/reschedule booking
- `POST /api/reviews` - Submit lawyer review

### 3. **Legal Articles & Knowledge Base**
- **Content Management**: CRUD operations for legal articles
- **Rich Media Support**: Handle text, images, and embedded content
- **Search & Indexing**: Full-text search across articles
- **Categorization**: Tag and categorize articles by legal topics
- **User Engagement**: Like, comment, and bookmark functionality
- **Author Management**: User and lawyer contribution systems
- **Trending Algorithm**: Calculate and surface popular content

**API Endpoints:**
- `GET /api/articles` - List articles with pagination and filters
- `GET /api/articles/:id` - Get article details
- `POST /api/articles` - Create new article
- `PUT /api/articles/:id` - Update article
- `POST /api/articles/:id/like` - Like/unlike article
- `POST /api/articles/:id/comments` - Add comment

### 4. **Anonymous & Identified Case Reporting**
- **Flexible Reporting System**: 
  - Support for anonymous case submissions
  - Identified reporting with user authentication
- **Case Management**: Track case status and updates
- **File Upload Service**: Handle evidence and document uploads (images, PDFs, documents)
- **Encryption**: End-to-end encryption for sensitive case data
- **Geolocation Services**: Location tagging for cases
- **Status Tracking**: Real-time case progress updates
- **Notification System**: Alert users of case status changes

**API Endpoints:**
- `POST /api/cases` - Submit new case (anonymous or identified)
- `GET /api/cases/:id` - Get case details
- `GET /api/cases/user/:userId` - Get user's cases
- `PUT /api/cases/:id/status` - Update case status
- `POST /api/cases/:id/attachments` - Upload case evidence

### 5. **Analytics Dashboard (NGO/Government Organizations)**
- **Data Aggregation**: Collect and process case data across regions
- **Statistical Analysis**: Generate insights from reported cases
- **Geographic Analytics**: Location-based case distribution
- **Trend Detection**: Identify patterns and emerging legal issues
- **Custom Reports**: Generate customizable analytical reports
- **Data Export**: Export data in multiple formats (PDF, Excel, CSV, JSON)
- **Real-time Updates**: WebSocket connections for live data
- **Access Control**: Role-based permissions for organizations

**API Endpoints:**
- `GET /api/analytics/overview` - Get summary statistics
- `GET /api/analytics/cases` - Get case analytics with filters
- `GET /api/analytics/trends` - Get trend analysis
- `GET /api/analytics/geographic` - Get location-based data
- `POST /api/analytics/reports` - Generate custom reports
- `GET /api/analytics/export` - Export analytical data

### 6. **Authentication & User Management**
- **Multi-role Authentication**: Support for users, lawyers, and organizations
- **JWT Token Management**: Secure token-based authentication
- **OAuth Integration**: Social login options
- **Email Verification**: Account verification system
- **Password Management**: Reset and recovery functionality
- **Session Management**: Handle multiple device sessions
- **Profile Management**: User profile CRUD operations

**API Endpoints:**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/users/profile` - Get user profile
- `PUT /api/users/profile` - Update user profile

## 👥 User Roles & Permissions

### Citizens/Users
- Access to ChatGPT-style legal chatbot
- Book consultations with lawyers
- Read and write legal articles
- Report cases (anonymously or with identity)
- Track their cases and consultations
- Manage profile and preferences

### Lawyers
- Professional profile management
- Accept/decline consultation requests
- Write and publish legal articles
- View client bookings and schedules
- Access analytics on their profile
- Respond to user inquiries

### NGOs/Government Organizations
- Access comprehensive analytics dashboard
- View aggregated case data (with privacy protections)
- Monitor legal trends and patterns
- Generate reports for policy making
- Plan intervention strategies
- Export data for external analysis

## 🛠️ Technical Stack

**Backend Framework**: 
- Node.js with Express.js / Python with Django/FastAPI / Ruby on Rails
- RESTful API architecture
- WebSocket support for real-time features

**Database**: 
- PostgreSQL (primary database for structured data)
- MongoDB (for chat history and unstructured data)
- Redis (caching and session management)

**AI/NLP Services**:
- OpenAI GPT-4 / Anthropic Claude / Google Gemini
- Custom fine-tuned models for legal domain
- LangChain for conversation management
- Vector database (Pinecone/Weaviate) for legal knowledge base

**Authentication**:
- JWT (JSON Web Tokens)
- OAuth 2.0 (Google, Facebook, Microsoft)
- bcrypt for password hashing

**File Storage**:
- AWS S3 / Google Cloud Storage / Azure Blob Storage
- Cloudinary for image optimization

**Real-time Communication**:
- Socket.io / WebSockets
- Server-Sent Events (SSE) for AI streaming responses

**Payment Processing**:
- Stripe / PayPal / Flutterwave / M-Pesa API

**Email Service**:
- SendGrid / AWS SES / Mailgun

**Cloud Services**:
- AWS / Google Cloud Platform / Microsoft Azure
- Docker for containerization
- Kubernetes for orchestration

**API Documentation**:
- Swagger/OpenAPI
- Postman collections

## 🚀 Getting Started

```bash
# Clone the repository
git clone https://github.com/sangwajesly/legalhub-backend.git

# Navigate to project directory
cd legalhub-backend

# Install dependencies
npm install
# or
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
npm run migrate
# or
python manage.py migrate

# Seed initial data (optional)
npm run seed

# Start development server
npm run dev
# or
python manage.py runserver

# Run tests
npm test
# or
pytest
```

## 📋 Environment Variables

```env
# Server
PORT=5000
NODE_ENV=development

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/legalhub
MONGO_URI=mongodb://localhost:27017/legalhub
REDIS_URL=redis://localhost:6379

# AI Services
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Authentication
JWT_SECRET=your_jwt_secret
JWT_EXPIRATION=24h
OAUTH_GOOGLE_CLIENT_ID=your_google_client_id
OAUTH_GOOGLE_CLIENT_SECRET=your_google_client_secret

# File Storage
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
S3_BUCKET_NAME=legalhub-uploads

# Email
SENDGRID_API_KEY=your_sendgrid_key
EMAIL_FROM=noreply@legalhub.com

# Payment
STRIPE_SECRET_KEY=your_stripe_key
STRIPE_WEBHOOK_SECRET=your_webhook_secret
```

## 📊 Database Schema

### Key Models:
- **Users**: User accounts and profiles
- **Lawyers**: Lawyer profiles and credentials
- **Organizations**: NGO/Government entity information
- **ChatSessions**: Conversation sessions
- **ChatMessages**: Individual chat messages
- **Cases**: Reported cases (anonymous and identified)
- **Bookings**: Lawyer consultation bookings
- **Articles**: Legal articles and content
- **Reviews**: Lawyer reviews and ratings
- **Analytics**: Aggregated data for insights

## 🔒 Security & Privacy

- **Encryption**: End-to-end encryption for sensitive data
- **HTTPS Only**: All API communication over TLS/SSL
- **Rate Limiting**: Prevent API abuse and DDoS attacks
- **Input Validation**: Sanitize all user inputs
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Content Security Policy headers
- **CORS Configuration**: Controlled cross-origin requests
- **Data Anonymization**: Privacy protection for anonymous cases
- **GDPR Compliance**: Data protection and user rights
- **Regular Security Audits**: Vulnerability assessments
- **API Authentication**: Token-based access control
- **Role-Based Access Control (RBAC)**: Permission management

## 📡 Real-time Features

- **Chat Streaming**: Stream AI responses token-by-token
- **Notifications**: Real-time alerts for bookings and case updates
- **Live Analytics**: Real-time dashboard updates for organizations
- **Typing Indicators**: Show when AI is generating response
- **Connection Status**: Display online/offline status

## 🧪 Testing

```bash
# Run all tests
npm test

# Run specific test suites
npm run test:unit
npm run test:integration
npm run test:e2e

# Generate coverage report
npm run test:coverage
```

## 📚 API Documentation

Once the server is running, access the API documentation at:
- Swagger UI: `http://localhost:5000/api-docs`
- Postman Collection: Available in `/docs/postman`

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

### Development Workflow:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

_[Add your license information]_

## 🔗 Related Repositories

- [LegalHub Frontend](https://github.com/sangwajesly/legalhub-frontend) - Web application interface

## 📞 Contact

For questions, suggestions, or support:
- **Email**: [Your contact email]
- **Website**: [Your website]
- **Issues**: [GitHub Issues](https://github.com/sangwajesly/legalhub-backend/issues)
- **Discord**: [Your Discord server]

## 🙏 Acknowledgments

- OpenAI / Anthropic for AI capabilities
- Open source community for various libraries and tools
- Legal professionals who provided domain expertise

---

**Mission**: Providing robust, scalable backend infrastructure that powers accessible legal services for everyone.
