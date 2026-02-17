# 🚀 Project Setup

The project can be launched in two ways: using Docker (recommended, especially for production) or locally on a development machine. The following guide focuses on the recommended method using Docker.

## Method 1: Running with Docker (Recommended)

This guide provides a comprehensive process for setting up and running the project on a virtual machine with Ubuntu, specifically prepared for a production environment. By following these instructions, you will install all necessary dependencies, configure the environment, and launch the application, minimizing the risk of errors.

---
### **Step 1: Install Docker and Docker Compose**

First, we need to install the Docker engine and the Docker Compose plugin. These tools will manage the application's services in isolated containers.

1.  **Update the package list and install dependencies:**
    ```bash
    sudo apt-get update
    sudo apt-get install ca-certificates curl
    ```

2.  **Add Docker's official GPG key to ensure package authenticity:**
    ```bash
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    ```

3.  **Add the Docker repository to the system's sources:**
    ```bash
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    ```

4.  **Install the Docker engine, command-line interface (CLI), and Docker Compose plugin:**
    ```bash
    sudo apt-get update
    sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    ```

---

### **Step 2: Configure Docker Permissions**

To run `docker` commands without `sudo` and avoid permission errors, you need to add your user to the `docker` group.

1.  **Add your current user to the `docker` group:**
    ```bash
    sudo usermod -aG docker $USER
    ```

2.  **Apply the changes.** For the new group membership to take effect, **you must restart the virtual machine**.
    ```bash
    sudo reboot
    ```
    After restarting the machine, log in and proceed to the next step.

---

### **Step 3: Install Git**

Git is required to download the project files from the repository.

1.  **Install Git using the package manager:**
    ```bash
    sudo apt-get install git -y
    ```

---

### **Step 4: Configure the Quiz App Project (Production Environment)**

Once all dependencies are ready, you can clone the repository and configure it for the production environment.

1.  **Clone the repository from GitHub:**
    ```bash
    git clone https://github.com/Zyrandool/Quiz-App
    cd Quiz-App
    ```

2.  **Configure environment variables in the `.env` file.**

    > **Note:** The following command uses the `nano` editor. If it's not installed, you can add it with `sudo apt-get install nano -y`.

    ```bash
    nano .env
    ```
    Copy and paste the following content into the file. **Remember to change the sensitive data!**

    ```env
    # Django Core Settings
    SECRET_KEY='paste_your_very_secure_key_here'
    DEBUG=0
    DJANGO_ALLOWED_HOSTS=your_domain.com,www.your_domain.com

    # Database Settings - CHANGE THE VALUES BELOW TO YOUR OWN!
    POSTGRES_DB=quiz_db
    POSTGRES_USER=quiz_user
    POSTGRES_PASSWORD='your_super_secure_database_password'

    # This variable is built automatically from the values above.
    DATABASE_URL=postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}

    # Celery Settings
    CELERY_BROKER_URL=redis://redis:6379/0
    CELERY_RESULT_BACKEND=redis://redis:6379/0

    # Gemini API Key (optional)
    GEMINI_API_KEY='your_gemini_api_key'
    ```
    **Important:**
    *   Generate a new `SECRET_KEY` with the command: `openssl rand -base64 48`.
    *   Set your own secure password in `POSTGRES_PASSWORD`.
    *   In `DJANGO_ALLOWED_HOSTS`, replace `your_domain.com` with your actual domain or public IP address.

---

### **Step 5: Launch the Application**

With the configuration in place, you can build the Docker images and run all services. SSL certificates for the database will be generated automatically.

1.  **Build and run the containers in the background:**
    ```bash
    docker compose up --build -d
    ```

2.  **Check the status.** Make sure all containers are running correctly.
    ```bash
    docker compose ps
    ```
    You should see a status of `running` or `up` for all services.

---

### **Step 6: Prepare Application Data**

After launching the containers, the database migrations will run automatically. You just need to load the quiz content.

1.  **Import quizzes into the database.** To import quizzes correctly, place the `.json` files in the `media/tests/` folder, as the Docker volume is configured to use this path.
    ```bash
    docker compose exec web python manage.py import_quizzes media/tests
    ```

2.  **(Recommended) Create a superuser.** This will allow you to log in to the Django admin panel (`/admin`).
    ```bash
    docker compose exec web python manage.py createsuperuser
    ```
    The program will prompt you to enter a username, email address, and password.

3.  **Done!** Your application is fully configured, running, and ready to use at your domain address.


### Method 2: Local Setup (for Windows Developers)

This method is intended for development and testing on a local machine. It uses an SQLite database and requires manual installation of some dependencies.

**Prerequisites:**
- **Python** (version 3.8 or newer)
- **Node.js** and **npm**
- **Redis** (required for Celery) - [Installation instructions for Windows](https://redis.io/docs/getting-started/installation/install-redis-on-windows/)

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Zyrandool/Quiz-App
    cd Quiz-App
    ```

2.  **Set up the Backend:**
    - Create and activate a virtual environment:
      ```bash
      python -m venv env
      .\env\Scripts\activate
      ```
    - Install Python dependencies:
      ```bash
      pip install -r requirements.txt
      ```

3.  **Set up the Frontend:**
    - Navigate to the `frontend` directory:
      ```bash
      cd frontend
      ```
    - Install Node.js dependencies:
      ```bash
      npm install
      ```
    - Return to the main project directory:
      ```bash
      cd ..
      ```

4.  **Run the development environment:**
    Use the provided script to run all components (Django, Vite, Celery) in a single Windows Terminal window.
    ```bash
    .\start_dev.bat
    ```
    - **Backend (Django)** will be available at `http://127.0.0.1:8000`.
    - **Frontend (Vite)** will be available at `http://localhost:5173`.
    - **Celery Worker** will run in the background, handling asynchronous tasks.