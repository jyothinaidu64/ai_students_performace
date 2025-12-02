

---

# **School Intelligence & Performance Management System**

### *AI-Powered Student Analytics, Dashboards, and Timetabling (Django + PostgreSQL + ML + OR-Tools)*

This is a full-stack, production-ready **School Intelligence Platform** designed for Indian academic institutions (LKG → 10th).
It brings together:

* Student Management
* Academic Performance Tracking
* AI/ML Risk Prediction
* Class-wise & Student-wise Dashboards
* Advanced Filtering, Search, CSV Exports
* Automated Timetable Generation (OR-Tools CP-SAT)
* Role-based authentication (Management / Class Teacher / Teacher / Student)
* Hybrid modern UI (Dark Sidebar + Light Content)
* Demo seeding: **LKG–10th**, **12 classes**, **360 students**

Built using:

* **Django 5+**, **PostgreSQL**, **Chart.js**, **Bootstrap 5**
* **scikit-learn**, **pandas**, **numpy**
* **OR-Tools** for timetable optimization
* Fully modular backend + clean UI templates

---

## 🔥 Features

### 🎯 **Role-Based Dashboards**

| Role              | Features                                                                                       |
| ----------------- | ---------------------------------------------------------------------------------------------- |
| **Management**    | Full school analytics, filters, risk distribution chart, subject performance chart, CSV export |
| **Class Teacher** | Class-only analytics, teacher copilot insights, risk summary, CSV export                       |
| **Student**       | Personal risk score, explanations, recommendations, subject performance chart + table          |

---

### 🤖 **AI/ML Components**

* Logistic Regression–based **risk prediction**
* Feature Engineering:

  * Avg marks %, attendance %, assignment completion
  * Marks variance, last test score
* **Risk explanations** + actionable recommendations
* **Model metadata tracking**:

  * accuracy, last trained time, sample count
* Auto-train during:

  * `python manage.py seed_school_data`
  * `python manage.py train_risk_model`

---

### 🏫 **Demo Data Seeder**

One command seeds the full school dataset:

```
python manage.py seed_school_data
```

It creates:

* 12 classes (LKG, UKG, 1 → 10)
* 1 class teacher per class
* 30 students per class → **360 students**
* 5 subjects
* Random but realistic assessments for all
* Trains ML model + writes metadata

---

### 📊 **Dashboards & Charts**

* Doughnut charts (risk distribution)
* Bar charts (subject-level performance)
* Student performance table
* Class-by-class analytics and sorting

---

### 📋 **CSV Export**

* Export filtered results
* Role-based (management and class teacher)

---

### 📅 **Timetable Engine**

* Google OR-Tools CP-SAT solver
* Teacher constraint rules
* Session distribution
* Conflict-free timetable generation
* Clean timetable grid UI

---

## 🛠️ Installation

### **Clone**

```
git clone https://github.com/yourname/school-intelligence.git
cd school-intelligence
```

### **Create Virtual Environment**

```
python3 -m venv venv
source venv/bin/activate
```

### **Install Dependencies**

```
pip install -r requirements.txt
```

---

### **Database Setup (SQLite)**

The project is configured to use **SQLite** by default for easy setup. No external database installation is required.
The database file `db.sqlite3` will be created automatically when you run migrations.

---

## ⚙️ Environment Variables

Create a `.env` file:

```
DEBUG=True
SECRET_KEY=replace_this_with_a_real_secret
# DB_NAME=school_intel
# DB_USER=school_user
# DB_PASSWORD=strongpassword
# DB_HOST=localhost
# DB_PORT=5432
```

---

## 🧱 Run Migrations

```
python manage.py makemigrations
python manage.py migrate
```

---

## 🌱 Seed Full School Dataset

```
python manage.py seed_school_data
```

This generates:

* 360 students
* Assessments
* All roles
* Fully trained ML model

---

## ▶️ Run Development Server

```
python manage.py runserver
```

Open:
👉 [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🔐 Default Demo Logins

### Management

```
username: admin_mgmt
password: admin123
```

### Class Teachers

```
ct_lkg, ct_ukg, ct_1, ct_2, ... ct_10
password: teacher123
```

### Students

```
gv10_01, gv10_02, ...
password: Password123
```

---

## 📦 Project Structure

```
students_performance/
│
├── accounts/            # Custom User model + roles
├── students/            # Students, Classes
├── assessments/         # Subjects, Assessments
├── analytics/           # ML model, dashboards, charts
│   ├── ml_utils.py      # ML pipeline + risk prediction
│   ├── management/commands
│   │     └── seed_school_data.py
│   └── templates/analytics/
│
├── timetable/           # OR-tools timetable generator
│
├── templates/           # base.html + login + homepage
│
├── static/css/main.css  # Hybrid theme
│
├── manage.py
└── requirements.txt
```

---

## 🚀 Roadmap

* AI agents for teachers ("Teacher Copilot")
* LSTM-based sequential student prediction
* Parent portal
* Behavior/attendance prediction
* Fee management module
* Blockchain-based verifiable report cards

---

## 🤝 License

MIT License – free for personal & commercial use.

---

## 👤 Author

**Ottigunta Jyothi Naidu**
Email: *ottiguntajyothi.naidu@gmail.com*
GitHub: *your GitHub profile*

---

---
