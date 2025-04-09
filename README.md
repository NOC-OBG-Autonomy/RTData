# c2py

Working on packaging functions to interact with the C2 rest API. 
Some other functions will be added, like interacting with ship MQTT broker or NKE float RT surface alert.
 
## Under construction

---

## How to use

### ***Option 1 - Setup without conda***

#### 1. **Clone the repository**

Start by cloning the repository to your local machine:

```bash
git clone https://github.com/yourusername/rtdata.git
cd rtdata
```

#### 2. **Install Poetry**
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

#### 3. **Install dependencies**
run
```bash
poetry install
```
This command will:

Set up a virtual environment (if one doesn't exist).
Install all necessary dependencies listed in the pyproject.toml file.
Poetry will automatically handle all dependencies and environment setup for you.

#### 4. **Activate the Virtual Env**

To work within the virtual environment Poetry created for your project, run:
```bash
poetry shell
```
This will activate the environment, and you can use your package directly.

#### Additional note

Do not forget to use the python venv created by poetry as your interpreter ;) 

### ***Option 2 - Setup with conda***

#### 0. **Install conda**

Conda can be installed either fully, or as a lighter distribution, Miniconda.
https://www.anaconda.com/download/success
Ensure to install conda to ROOT and as the default python interpreter.

#### 1. **Clone the repository**

Start by cloning the repository to your local machine:

```bash
git clone https://github.com/yourusername/rtdata.git
cd rtdata
```

#### 2. **Setup new conda environment for RT_data**

Within the conda or miniconda terminal, run the following command:

```
conda create --name RT_data python=3.12
```
This assumes you don't already have an environment named RT_data, and will setup the environment with Python 3.12, a requirement for this tool package.

#### 3. **Install poetry within your conda environment***

Within the conda or miniconda terminal, run the following command:
(If you named your environment something other than RT_data, replace the 'RT_data' in this line with your environment name)

```
conda activate RT_data
```

Next, install the poetry package manager to your conda environment:

```
conda install conda-forge::poetry
```

#### 4. **Install dependancies with poetry**

Now, working within 'rtdata' directory, run the follwing:

```
poetry install
```

This will install all the required dependancies to run the package