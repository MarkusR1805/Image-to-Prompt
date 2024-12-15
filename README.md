<div align=center><h1>Prompt from picture with Image-to-Prompt</h1></div>

## The old version ‘main.py’ has been replaced by the former version ‘main2.py’! From now on you can select at least 2 vision models, and if you change the code, you can also add more.
## Supported image formats: jpg, jpeg, png, bmp
Install Ollama
<http://ollama.com>

For main.py please install 2 models

```sh
ollama pull llama3.2-vision
```
```sh
ollama pull llava:7b
```

Install Git
<https://git-scm.com/downloads>

Install Python
<https://www.python.org/downloads/>

<h2>Clone Repository</h2>

```sh
git clone https://github.com/MarkusR1805/Image-to-Prompt.git
```

<h2>OPTIONAL!! Create python venv</h2>

```sh
python -m venv llama3.2-vision
cd llama3.2-vision
source bin/activate
```

<h1>Attention, very important!</h1>
If the program does not start or an error message appears, be sure to execute the requirements.txt.

```sh
pip install --upgrade pip
pip install -r requirements.txt
```

<h2>Programm start</h2>

```sh
python main.py
```

![Promptgenerator](https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/26f2122f-6738-45e1-bcf9-0e62f281622c/original=true,quality=90/36686347.jpeg)
