# Interactive AI

![Python](https://img.shields.io/badge/Python-3.12%2B-blue?style=flat&logo=python)
![Docker](https://img.shields.io/badge/Docker-Required-2496ED?style=flat&logo=docker)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)
![API](https://img.shields.io/badge/API-OpenAI%20Compatible-412991?style=flat&logo=openai)

Interactive AI is an autonomous digital worker designed to turn natural language requests into executed technical tasks, making complex system administration and development accessible to users of all skill levels. Unlike a traditional chatbot that only offers text advice, this agent possesses full root privileges within a secure, isolated Docker environment, allowing it to actively install software, write code, configure networks, and manage files via SSH just like a human engineer. Powered by advanced Large Language Models, it understands intent and autonomously formulates plans to solve a vast array of challenges, from deploying web applications and analyzing data to joining Minecraft server or processing media files. The system comes pre-loaded with a comprehensive toolkit including Python, Java, ffmpeg, and networking utilities, but it also has the agency to download and install new tools as needed to get the job done. By operating in a sandboxed container, it provides a safe playground for experimentation and automation, executing your commands efficiently while keeping main machine protected from accidental changes.

## 📸 Demo

![Network Diagnostics](https://i.imgur.com/xj08xbe.png)

<details>
  <summary><b>Click to see more examples</b></summary>

  ### Joining Minecraft Server
  ![Joining Minecraft Server](https://i.imgur.com/BOnylIM.jpeg)

  ### Web Scraping
  ![Web Scraping](https://i.imgur.com/ZVgBkwU.png)

  ### Ping Check
  ![Ping Check](https://i.imgur.com/Rtuausv.png)

  ### Server Interaction
  ![Server Interaction](https://i.imgur.com/uIJjbvz.png)
</details>

## 🚀 Get Started

Follow these steps to set up your autonomous agent.

### Prerequisites

* **Docker** (Must be installed and running)
* **Python 3.12+**
* **OpenRouter API Key** (Get it [here](https://openrouter.ai/settings/keys))

> **Linux Users:** Depending on your configuration, you may need to prepend commands with `sudo` to interact with the Docker daemon.

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Kartoshka2331/interactive-ai.git
    cd interactive-ai
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup the Environment** — Run the automated setup script. This will build the isolated Docker image and create necessary directories:
    ```bash
    python setup_env.py
    ```

4.  **Configuration** — Open the newly created `.env` file and paste your API key:
    ```ini
    OPENROUTER_API_KEY=sk-or-your-key-here
    ```

## ⚡ Usage

1.  **Start the System** — This launches the backend server and the isolated Docker container:
    ```bash
    python start_system.py
    ```

2.  **Run the Demo-client** — Open a new terminal window and start the interactive CLI:
    ```bash
    python client.py
    ```

## 📚 API Reference

This project exposes an **OpenAI-compatible API**, meaning you can use standard OpenAI libraries to interact with it.

#### Get Chat Completion

```http
  POST /v1/chat/completions
```

| Parameter | Type | Description |
| --- | --- | --- |
| `messages` | `array` | **Required**. A list of messages comprising the conversation history. |
| `stream` | `boolean` | **Optional**. If set to `true`, partial message deltas will be sent. Default is `false`. |
| `temperature` | `float` | **Optional**. Controls randomness (0.0 to 2.0). Default is `1.0`. |
| `model` | `string` | **Optional**. The model ID to use (e.g., `google/gemini-2.0-flash-001`). See [supported models](https://openrouter.ai/models?fmt=cards&supported_parameters=tools). |

---

<div align="center"> <sub>Built with ❤️ by Kartoshka2331. Released under the MIT License.</sub> </div>
