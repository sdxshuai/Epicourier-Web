# Epicourier-Web 🍽️

[![CI/CD Pipeline](https://github.com/sdxshuai/Epicourier-Web/actions/workflows/ci-jest.yml/badge.svg)](https://github.com/sdxshuai/Epicourier-Web/actions/workflows/ci-jest.yml)
[![codecov](https://codecov.io/github/sdxshuai/Epicourier-Web/graph/badge.svg?token=TTLT1APZ44)](https://codecov.io/github/sdxshuai/Epicourier-Web)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17537732.svg)](https://doi.org/10.5281/zenodo.17537732)
[![Project Status: Active](https://img.shields.io/badge/status-active-brightgreen.svg)](#)

**YOUR NUTRITION, YOUR CONTROL. AI-POWERED MEAL PLANNING FOR WELLNESS AND SUSTAINABILITY.**

Epicourier is a comprehensive, full-stack web ecosystem designed to modernize the culinary lifestyle. It seamlessly integrates AI-driven recipe generation with advanced inventory management. While the platform automates the logic of meal planning, our latest expansion focuses on the execution: tracking nutrition, gamifying consistency, and optimizing grocery logistics to reduce waste and enhance user engagement.

---

## 🎬 Demo Video

**Watch our project demonstration on YouTube:**

<div align="center">
  
[![Epicourier Demo Video](https://img.youtube.com/vi/qbFYmMTnb5M/maxresdefault.jpg)](https://youtu.be/qbFYmMTnb5M)

**[▶️ Watch on YouTube](https://youtu.be/qbFYmMTnb5M)** | Full Features Demo

</div>

---

## ✨ New Features (Phase 2 Expansion)

### 📊 1. Nutrient Command Center

_Data-driven health insights._

- **Interactive Analytics**: A fully responsive dashboard powered by **Recharts** to visualize daily, weekly, and monthly macro trends.
- **Goal Setting**: Users can define and track custom daily nutrient targets stored via immutable database indexing.
- **Portability**: Full support for data export (CSV/Text reports) for healthcare or personal archiving.

### 🎮 2. Gamified Wellness Architecture

_Making healthy habits addictive._

- **Streak System**: Visual "flame" intensity scales based on consistency, complete with "At Risk" warnings to prevent habit breaking.
- **Challenges & Badges**: A robust engine for Weekly/Monthly challenges. Users unlock tier-based badges tracked via a dedicated achievement schema.
- **Social & Engagement**: Real-time progress bars and participation UI to keep motivation high.

### 🛒 3. AI Smart Cart & Inventory Manager

_Reduce waste, save money._

- **Intelligent Inventory**: Track pantry/fridge items with automatic expiration color-coding (Green/Yellow/Red alerts).
- **Gemini-Powered Suggestions**: Our Python API utilizes **Google Gemini 2.5 Flash** to recommend recipes based specifically on ingredients expiring soon to minimize waste.
- **Seamless Logistics**: One-click generation of shopping lists from meal plans, with automatic transfer flow from "Shopping List" to "User Inventory" upon purchase.

**Tests**: 1,130+ automated test cases covering UI interactions, gamification logic, and backend AI services (Jest/Pytest). Pipelines: End-to-end GitHub Actions workflows for instant formatting (Ruff/Prettier), linting, and unit verification.

---

## 🚀 Getting Started

Ready to cook? Follow these guides to set up your environment.

- **📥 Installation**: Step-by-step setup guide. 👉 [INSTALL.md](INSTALL.md)
- **🤝 Contribution**: Join the team! 👉 [CONTRIBUTE.md](CONTRIBUTE.md)
- **🤖 Agent Guide**: For AI agents working on this repo. 👉 [AGENT-PLAN/00-QUICK-START.md](AGENT-PLAN/00-QUICK-START.md)

---

## 🧩 Tech Stack

### 🌐 Web App (Frontend)

Built with a modern TypeScript-based stack for reliability, scalability, and developer productivity.

| Category            | Tools                                                                                                             |
| ------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Framework           | [![Next.js](https://img.shields.io/badge/Next.js-black?logo=next.js&logoColor=white)](#)                          |
| Styling             | [![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-%2338B2AC.svg?logo=tailwind-css&logoColor=white)](#) |
| Language            | [![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=fff)](#)                  |
| Code Syntax Checker | [![ESLint](https://img.shields.io/badge/ESLint-3A33D1?logo=eslint&logoColor=fff)](#)                              |
| Code Style Checker  | [![Prettier](https://img.shields.io/badge/Prettier-1A2C34?logo=prettier&logoColor=F7BA3E)](#)                     |
| Testing             | [![Jest](https://img.shields.io/badge/Jest-C21325?logo=jest&logoColor=fff)](#)                                    |
| Visualization       | [![Recharts](https://img.shields.io/badge/Recharts-22b5bf?style=flat&logo=recharts&logoColor=white)](#)           |

---

### ⚙️ Backend (FastAPI Service)

Serves model inference, powered by FastAPI.

| Category                | Tools                                                                                                                                                                                                        |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Language                | [![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)](#)                                                                                                                         |
| Framework               | [![FastAPI](https://img.shields.io/badge/FastAPI-009485.svg?logo=fastapi&logoColor=white)](#)                                                                                                                |
| Database                | [![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white)](#) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?logo=postgresql&logoColor=white)](#)              |
| Model                   | ![Google Gemini](https://img.shields.io/badge/google%20gemini-8E75B2?logo=google%20gemini&logoColor=white) ![HuggingFace](https://img.shields.io/badge/-HuggingFace-FDEE21?logo=HuggingFace&logoColor=black) |
| Testing                 | [![Pytest](https://img.shields.io/badge/Pytest-fff?logo=pytest&logoColor=000)](#)                                                                                                                            |
| Automated Analysis Tool | [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)                                                 |

---

## 🧪 Coverage

Code coverage is automatically tracked via **Codecov**:

[![codecov](https://codecov.io/github/sdxshuai/Epicourier-Web/graph/badge.svg?token=TTLT1APZ44)](https://codecov.io/github/sdxshuai/Epicourier-Web)

---

## 📊 Dataset

For details about dataset construction and preprocessing, please refer to:
👉 [data/README.md](data/README.md)

---

## 📜 Citation

If you use this repository or dataset in your work, please cite it as:

> Epicourier Team. (2025). _Epicourier-Web_ [Computer software]. Zenodo.  
> [https://doi.org/10.5281/zenodo.17537732](https://doi.org/10.5281/zenodo.17537732)

---

## 📎 License

This project is released under the [MIT License](LICENSE).

---

## 📘 Documentation

More details and technical notes are available in the [Wiki Documentation](https://github.com/epicourier-team/Epicourier-Web/wiki).
