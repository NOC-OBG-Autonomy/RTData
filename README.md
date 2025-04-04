# c2py

Working on packaging functions to interact with the C2 rest API. 
Some other functions will be added, like interacting with ship MQTT broker or NKE float RT surface alert.
 
## Under construction

---

## How to use

### 1. **Clone the repository**

Start by cloning the repository to your local machine:

```bash
git clone https://github.com/yourusername/rtdata.git
cd rtdata
```

### 2. **Install Poetry**
If you don't have poetry run the following commands 

**macOS/Linux:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Windows (Powershell)**
```Powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

**Pipx**
```bash
pipx install poetry
```

### 3. **Install dependencies**
run
```bash
petry install
```
This command will:

Set up a virtual environment (if one doesn't exist).
Install all necessary dependencies listed in the pyproject.toml file.
Poetry will automatically handle all dependencies and environment setup for you.

### 4. **Activate the Virtual Env**

To work within the virtual environment Poetry created for your project, run:
```bash
poetry shell
```
This will activate the environment, and you can use your package directly.

### Additional note

Do not forget tu use the python venv created by poetry as your interpreter ;) 
