# 🤖 BlueWave AI Support

This repository contains the backend code and frontend integration documentation for the BlueWave Robotics intelligent support chatbot. This system is developed based on the RAG (Retrieval-Augmented Generation) architecture and the FastAPI framework, serving users as a floating widget on WordPress.

## 🏗 Project Structure

The project consists of the following main components:

* `main.py`: The core FastAPI-based web server that receives requests from WordPress, processes them, and returns responses after converting Markdown to standard HTML (including link buttons).
* `rag_core.py`: The search and information retrieval engine (RAG) that matches user queries with the company's knowledge base and sends them to the LLM.
* `bluewave_knowledge_base_V6.txt`: The text knowledge base containing all technical specifications, datasheets, and setup guides for products (BlueMind, BlueLab, BlueMCU, sensors, etc.).
* `wordpress_widget.php`: Client-side code (HTML/CSS/JS) injected into WordPress via the Code Snippets plugin to build the chatbot UI.

## 🚀 Deployment and Server Update Guide

For initial deployment or applying new changes from GitHub on a Linux server, run the following steps in sequence in the server terminal:

### 1. Fetch latest changes from GitHub
```bash
cd /opt/AI-projects/wordpress_ai_support
git fetch origin
git reset --hard origin/main
git pull origin main
```

### 2. Stop the previous service
Before running the new version, previous server processes must be stopped:
```bash
pkill -f uvicorn
```

### 3. Install dependencies
Activate the virtual environment and install dependencies (e.g., if new libraries like `markdown` were added):
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Update the Knowledge Base (RAG)
**Important:** If any content in the knowledge base (`bluewave_knowledge_base_V6.txt`) has been modified, you must run the following command to rebuild the vector database:
```bash
python3 rag_core.py
```

### 5. Run the server in the background
Start the server using `nohup` so it continues running after you close the terminal:
```bash
nohup uvicorn main:app --host 127.0.0.1 --port 8000 > output.log 2>&1 &
```
*(To view potential errors or server logs, you can use the command `tail -n 20 output.log`).*

## 💻 WordPress Integration

To display the chatbot on your website, the code provided in the `wordpress_widget.php` file must be inserted into the `wp_footer` section of your WordPress site using the **Code Snippets** plugin. 
This code includes:
- Responsive CSS styles (optimized for both desktop and mobile views).
- JavaScript logic for toggling the chat window seamlessly (preventing Event Bubbling conflicts).
- Secure API communication with the backend and rendering of HTML buttons returned by Python.

## 👨‍💻 Developer
Developed by **Mohammad Rahimi** for Parsian Robotic Systems Technology Development Company (BlueWave Robotics).