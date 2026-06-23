# SIRO HR Chatbot – Frontend  
React + TypeScript + Vite + Material UI

This repository contains the frontend of the **Human Resources Chatbot Project** developed for **Siro Energy** as part of **Sabancı University ENS491/492 Senior Design Project**.

The interface communicates with a backend RAG system (FastAPI) and provides a clean, modern chat experience using Material UI.

---

## 🚀 Features
- Chat-based HR assistant UI  
- Material UI design  
- Message bubbles, history, sidebar  
- API integration through Axios  
- TypeScript support  
- Fast Vite development server  

---

## 📦 Installation

```bash
git clone https://github.com/atarikguner/siro_chatbot_FE.git
cd siro_chatbot_FE
npm install
npm run dev
```

Open the app at:
```
http://localhost:5173
```

---

## 🔗 Backend Connection

Update `src/services/api.ts`:

```ts
export const API_URL = "http://127.0.0.1:8000";
```

---

## 🧩 Project Structure

```
src/
│── components/
│── pages/
│── services/
│── App.tsx
└── main.tsx
```

---

## 👥 Team
- Ahmet Tarık Güner  
- Burç Güven  
- Salih Kobaş  

---

## 🛠 Development Workflow

Each teammate should create a feature branch:

```bash
git checkout -b burc/ui-update
git push -u origin burc/ui-update
```

Pull Requests will be merged into `main`.

---
