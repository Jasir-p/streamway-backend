# 🚀 Streamway CRM – Simplifying Business Management

## 📘 Overview

**Streamway CRM** is a multi-tenant, cloud-based customer relationship management platform built to streamline and scale operations for businesses that follow both **B2B** and **B2C** strategies.
Designed for adaptability and growth, Streamway CRM empowers organizations to manage leads, deals, tasks, and communications while maintaining a personalized experience for each tenant.

---

## 🔧 Features

### 💬 Group Chat & Team Creation

Collaborate seamlessly with internal teams using real-time group messaging.
Keep internal communication centralized and reduce the need for external tools like Slack or WhatsApp.

### 🗘 Task Management with Auto Mail Reminders

Automate follow-ups and reminders to boost productivity.
Helps teams stay accountable and never miss important follow-ups.

### 📢 Mass Email Campaigns

Send bulk emails to customers, leads, or team members for promotions or updates.
Ideal for running promotions, onboarding new users, or sending critical notifications.

### 📊 Lead & Deal Tracking

Effectively monitor and manage your sales pipeline.
Gain insights into conversion performance and optimize your sales strategy.

### 📄 Customizable Forms

Tailor data collection forms to meet your tenant's specific operational needs.
Perfect for collecting structured data like enquiries, registrations, or custom workflows.

### 📅 Meeting Scheduling with Slot Booking

Schedule meetings and allow users to book available time slots based on predefined availability.
Ideal for sales calls, client onboarding, or internal check-ins without scheduling conflicts.

### 🔐 Dynamic Role-Based Access Control (RBAC)

Configure user roles and permissions flexibly for every tenant.
Ensure secure, structured access for employees at every level.

### 🏢 Multi-Tenant Architecture

Each tenant has isolated data, permissions, and control to manage their business operations independently.
Ideal for SaaS platforms serving multiple clients on a single codebase.

### 📥 Lead Capture & Enquiry Conversion

Capture inbound enquiries and seamlessly convert them into leads for follow-up and assignment.
Streamlines the lead generation process and ensures no opportunity is missed.

---

## 🛠 Admin Dashboard

* Tenant management
* Real-time analytics and engagement tracking
* Activity and access logs per tenant
* Billing and subscription management
* Role and permission configuration
* Announcement creation and platform-level control

---

## 🛠️ Tech Stack

### 🔹 Frontend

* **React & Redux Toolkit** – Modern UI with efficient state management
* **Tailwind CSS** – Utility-first CSS framework
* **Axios** – Promise-based HTTP client
* **WebSocket** – Real-time features like chat and live updates

### 🐍 Backend

* **Django-Tenants** – Multi-tenant isolation and schema management
* **Django REST Framework (DRF)** – Secure, modular REST APIs
* **Django Channels** – WebSocket support for real-time communication
* **PostgreSQL** – Scalable relational database
* **Redis** – Caching and real-time processing
* **Celery & Celery Beat** – Background task management
* **Stripe** – Subscription billing and payment handling

### ⚙️ DevOps & Deployment

* **Docker & Docker Compose** – Consistent container-based development
* **Nginx (within Docker)** – Reverse proxy and load balancing
* **AWS EC2** – Scalable cloud hosting infrastructure

---

## 📦 Installation

### 🐍 Backend Setup

```bash
cd Server
python -m venv venv
source venv/bin/activate        # For Linux/Mac
venv\Scripts\activate           # For Windows

pip install -r requirements.txt
python manage.py migrate
daphne streamway.asgi:application
```

### 🌐 Frontend Setup

```bash
cd Client
npm install
npm run dev
```

### 🐳 Run Using Docker

```bash
docker-compose up --build
```

---

## 🔍 API Overview

* RESTful architecture
* JWT authentication
* WebSocket support for real-time chat
* API rate limiting for abuse protection

---

## 🛡 Security Measures

* Secure authentication & authorization
* CORS protection
* Input validation & rate limiting
* CSRF protection

---

## 📊 Monitoring & Analytics

* Error tracking & logging
* Database performance monitoring
* Web traffic analytics

---

## 🤝 Community & Support

For any queries or contributions:

* GitHub: [https://github.com/Jasir-p](https://github.com/Jasir-p)
* Email: [jazjasir7@gmail.com](jazjasir7@gmail.com)

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
