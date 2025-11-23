# Architectural Overview for the Polish Looted Art Finder Application (Pilot)

The goal of the pilot is to build a minimal viable product (MVP) that leverages existing public databases, alerts users to possible matches, and provides a straightforward interface for art provenance researchers, institutions, and the general public. The system should be scalable, secure, and easy to extend as more data and features are added in future iterations.

## 1. Data Ingestion Layer

This layer will handle the ingestion of data from various sources. The key data sources for this MVP will include the **Polish Ministry of Culture's war loss registry**, **auction house catalogs**, and publicly available provenance databases (for example, the [Lost Art Database](https://www.lostart.de/en/)).

### Components:
- **Web Scrapers** (for auction catalogs and online databases)
  - **Technology**: Python (BeautifulSoup, Scrapy), Node.js (Puppeteer) for scraping data from auction houses and art institutions.
  - **Functionality**: Periodically pull data from public databases and auction house listings, focusing on works from the Polish registry of war losses.
- **Data Importers/ETL Jobs** (for structured data from registries)
  - **Technology**: Python scripts, ETL tools like Apache Nifi, Talend, or custom scripts to pull data from structured sources (e.g., CSV, JSON).
  - **Functionality**: Extract and load the Polish Ministry's registry and other partner datasets, transforming the data into a normalized format for easy searching.
- **API Integrations** (if available)
  - **Technology**: REST APIs for direct integration with databases like the Lost Art Database, UNESCO, etc.
  - **Functionality**: Automated syncing with public databases where APIs are available, ensuring real-time or regular updates.

---

## 2. Data Normalization & Storage Layer

This layer is responsible for storing, indexing, and ensuring the integrity of the provenance data. It will involve some data transformation to standardize the format for easier matching.

### Components:
- **Database** (Relational and NoSQL)
  - **Technology**: PostgreSQL (for relational data storage like object metadata, item details, and provenance history), Elasticsearch (for fast search queries and text-based matching).
  - **Functionality**: Store normalized data from the war loss registry, auction catalogs, and provenance records.
  - **Design**:
    - Tables for `Items`, `Provenance Records`, `Auction Results`, `Users`, `Alerts`, etc.
    - Elasticsearch indexes for textual search (e.g., artist name, dimensions, date of loss).
- **Data Validation** (for ensuring consistency across sources)
  - **Technology**: Custom validation scripts or use of middleware frameworks to verify data quality (e.g., unique identifiers, correct formats).
  - **Functionality**: Ensure data integrity by checking for duplicate records, invalid provenance data, and incomplete entries.

---

## 3. Data Matching / AI Layer

In this pilot phase, the system will rely on basic matching algorithms for finding possible matches between "lost" items and items being sold at auctions or displayed in galleries. As the system evolves, machine learning and AI techniques could be integrated for more sophisticated matching.

### Components:
- **Record Linkage (Matching Algorithm)**
  - **Technology**: Python (FuzzyWuzzy, RecordLinkage toolkit, or custom algorithm).
  - **Functionality**: Perform fuzzy matching of item details such as artist name, title, size, and date. Matches will be scored based on confidence and proximity of key attributes.
  - **Design**: Use a scoring system for how closely an item matches a missing object in the registry (e.g., similarity score > 80% indicates a potential match).
- **Machine Learning/AI (future)**
  - **Technology**: TensorFlow or HuggingFace Transformers for NLP-based matching (if integrating textual provenance information).  
  - **Functionality**: In the long-term, the goal is to incorporate AI models for deeper pattern recognition and complex provenance trails.

---

## 4. User Interface (UI)

The user interface (UI) will be a web-based application that allows users (both public and institutional users) to search the database, receive alerts, and submit findings or provenance information.

### Components:
- **Search Interface**
  - **Technology**: React.js or Vue.js for the frontend (with Bootstrap or Material-UI for design).
  - **Functionality**: Allow users to search for missing artwork by various attributes (e.g., artist, dimensions, medium, year). Use Elasticsearch to power fast, flexible search.
- **Alert System**
  - **Technology**: React.js (Frontend) + Python (Backend), with email notifications powered by **SendGrid** or **Amazon SES**.
  - **Functionality**: Users can subscribe to alerts for specific artists, time periods, or categories of work. If a new potential match is found in the data, subscribers are notified by email or app notification.
- **Admin Panel** (for managing user accounts and alerts)
  - **Technology**: React.js for frontend, Express.js for backend services.
  - **Functionality**: Admin users can review new data entries, moderate user-submitted content, and manage alerts.

---

## 5. Backend / API Layer

The backend will handle all core business logic, data access, and external integrations. This includes managing user accounts, executing search queries, and interfacing with the data layer.

### Components:
- **API Layer**
  - **Technology**: Node.js (Express.js) or Python (Flask/Django).
  - **Functionality**: Provide endpoints for searching the database, managing user alerts, submitting new provenance data, etc.
  - **Endpoints**:
    - `GET /search`: Search for matching artworks by various criteria.
    - `POST /alert`: Subscribe users to alerts for specific criteria.
    - `POST /provenance`: Allow institutions and individuals to upload provenance information or claims.
- **Authentication & Authorization**
  - **Technology**: OAuth2 or JWT (JSON Web Tokens) for user authentication and authorization.
  - **Functionality**: Users need to authenticate to submit data, claim items, or receive alerts. Admins can manage submissions and moderate content.

---

## 6. Notification and User Engagement Layer

This layer will ensure that users are notified of relevant matches and other important updates.

### Components:
- **Notification System**
  - **Technology**: Email notifications via **SendGrid** or **Amazon SES**, WebSocket for in-app notifications.
  - **Functionality**: When a new potential match is found, or when a user submits valuable information, they receive email or in-app notifications. Alerts can be tailored based on user preferences (e.g., specific artists, auction results).
- **User Profiles & Preferences**
  - **Technology**: Database schema for user preferences, implemented with React.js (frontend) and Node.js/Python (backend).
  - **Functionality**: Users can create profiles and specify what types of notifications and alerts they want to receive.

---

## 7. Monitoring & Logging

Monitoring and logging will ensure that the system is stable, scalable, and transparent, providing insight into user behavior, errors, and performance metrics.

### Components:
- **Log Management**
  - **Technology**: ELK Stack (Elasticsearch, Logstash, Kibana) or **AWS CloudWatch** for centralized logging.
  - **Functionality**: Capture logs from the application and back-end services to monitor system health, debug errors, and track user activity.
- **Performance Monitoring**
  - **Technology**: Prometheus/Grafana, NewRelic.
  - **Functionality**: Monitor the performance of critical system components like the search engine (Elasticsearch), database queries, and backend APIs.

---

## 8. Security Layer

Security will be critical for the system, especially given the sensitive nature of the data involved (e.g., provenance claims, private auction listings, user details).

### Components:
- **Data Encryption**
  - **Technology**: SSL/TLS encryption for data in transit, encryption-at-rest using **AES** or **PGP** for sensitive user and provenance data.
  - **Functionality**: Ensure that all communications are encrypted and that sensitive data (e.g., user accounts, provenance claims) is securely stored.
- **Access Controls**
  - **Technology**: Role-based access control (RBAC).
  - **Functionality**: Admin users have different permissions than general users (e.g., moderation, submission management).

---

## Architecture Diagram

Here’s a simplified high-level architecture diagram for this pilot:

