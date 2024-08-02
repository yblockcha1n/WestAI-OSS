# WestAI
 In this WestAI OSS repo, this BOT is actually working in a discord community called **[Web3学生トーク](https://x.com/Web3studenttalk)** where high school students, university students, and adults can discuss Web3 and the latest techs, and promote the Metaverse😸

You are hereby authorized to build and customize freely using this repo.

<img src="https://github.com/user-attachments/assets/8dd52550-92f1-4a9e-8d59-c343624ce6e1" width="500">

(Generated at StableDiffusion Animagine XL 3.0 model)

## BOT Commands

| Command | Description |
| --- | --- |
| /ask | Asks a question to the AI, optionally considering attached files (including images) and saving the response as a text file |
| /change_model | Changes the AI model being used for responses. |
| /change_text | Changes the maximum number of characters for TTS conversion. |
| /current_model | Displays the currently active AI model. |
| /fix_list | Displays the current list of pronunciation fixes. |
| /fix_reading | Adds or updates a word's pronunciation in the TTS system. |
| /join | Makes the bot join the user's current voice channel. |
| /leave | Makes the bot leave the current voice channel. |
| /reset_conversation | Resets the conversation history for the user. |
| /summarize_youtube | Summarizes the content of a YouTube video, with an optional custom system prompt. |

> [!NOTE]
> This is a list of commands as of August 2024.

## Standard Supporting Models
| ChatGPT | Claude |
----|---- 
| GPT-4o | 3.5 Sonnet |
| GPT-4 | 3 Sonnet |
| GPT-3.5-Turbo | Opus |
|  | Haiku |

If you would like to add other models, please add them in the model selection section.

### Example: I want to add ChatGPT's GPT4 Turbo

```python
#モデル選択
class ModelChoices(discord.Enum):
    GPT_4_TURBO = "gpt-4-turbo"

CHATGPT_MODELS = [ModelChoices.GPT_4_TURBO]
```

Note that by default, ChatGPT's GPT-4 model is defined as the initial global variable.

```python
#標準モデルのグローバル変数
CURRENT_AI = "ChatGPT"
CURRENT_MODEL = "gpt-4"
```

### Reference Model Document
[Models - OpenAI API](https://platform.openai.com/docs/models)

[Models - Anthropic](https://docs.anthropic.com/en/docs/about-claude/models)

## Setting API Keys

### Required API Keys

- OpenAI_API_KEY
- Anthropic_API_KEY
- ElevenLabs_API_KEY

Link to get API Key

[OpenAI](https://openai.com/index/openai-api/)
[Anthropic](https://console.anthropic.com/)
[ElevenLabs](https://elevenlabs.io/api)

### Setting to config.json

```json
{
    "DISCORD_TOKEN": "YOUR_DISCORD_BOT_TOKEN",
    "OPENAI_API_KEY": "YOUR_OPENAI_API_KEY",
    "ANTHROPIC_API_KEY": "YOUR_ANTHROPIC_API_KEY",
    "ELEVENLABS_API_KEY": "YOUR_ELEVENLABS_API_KEY",
    "VOICE_ID": "YOUR_ELEVENLABS_VOICE_ID",
    "MAX_TTS_LENGTH": 1000,
    "LISTENING_STATUS": "Web3学生トーク"
}
```

> [!TIP]
> This script keeps the API Keys as a config file, but when hosting with other services (AWS, Railway, etc.), please have it as an env.

## Deploy (Vanilla Python Build)

### Step1: Clone this Repo & Create pyenv

**Clone & directory**
```
git clone https://github.com/yblockcha1n/WestAI-OSS
cd WestAI-OSS
```

**Create pyenv & activate**

MacOS & Linux
```
python -m venv venv
source venv/bin/activate
```

Windows
```
python -m venv venv
.\venv\Scripts\activate
```

### Step2: Install require library
```
pip install requirements.txt
```

> [!IMPORTANT]
> If you do not have ffmpeg installed, follow the instructions below.

MacOS & Linux
```
brew install ffmpeg
```

Windows

1. Download the build for Windows from the official [FFmpeg website](https://ffmpeg.org/download.html)

2. Unzip the downloaded zip file.

3. Locate the bin folder in the unzipped folder and copy its path.

4. Type "environment variables" in the Windows search bar and select "Edit System Environment Variables".

5. Click "Environment Variables," select the "Path" variable, and click "Edit.

6. Click "New" and paste the copied path.

7. Click OK to close all windows.

8. Open a command prompt and type `ffmpeg -version` to confirm installation.

### Step3: Run
```
python main.py
```

## Deploy (Docker)

### Step1: Clone this Repo & Docker Build

**Clone & directory**
```
git clone https://github.com/yblockcha1n/WestAI-OSS
cd WestAI-OSS
```

**Build Docker container**
```
docker build -t west-ai .
```

<details>

<summary>Build Log</summary>

```
[+] Building 243.4s (14/14) FINISHED                                                                                                                                                                    docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                                                                                    0.0s
 => => transferring dockerfile: 435B                                                                                                                                                                                    0.0s
 => [internal] load metadata for docker.io/library/python:3.11-slim-buster                                                                                                                                              0.9s
 => [internal] load .dockerignore                                                                                                                                                                                       0.0s
 => => transferring context: 2B                                                                                                                                                                                         0.0s
 => [1/9] FROM docker.io/library/python:3.11-slim-buster@sha256:c46b0ae5728c2247b99903098ade3176a58e274d9c7d2efeaaab3e0621a53935                                                                                       43.6s
 => => resolve docker.io/library/python:3.11-slim-buster@sha256:c46b0ae5728c2247b99903098ade3176a58e274d9c7d2efeaaab3e0621a53935                                                                                        0.1s
 => => sha256:482d64d97d4e63625e51301e23ca7ff526afaf40710da26704d9ce2e1a6168fa 12.00MB / 12.00MB                                                                                                                        4.4s
 => => sha256:c46b0ae5728c2247b99903098ade3176a58e274d9c7d2efeaaab3e0621a53935 988B / 988B                                                                                                                              0.0s
 => => sha256:b94af75d4ff65c50bf1b2119bca6d0ba707037bacd0cb75314801a6953c03241 1.37kB / 1.37kB                                                                                                                          0.0s
 => => sha256:db841a2e8ab326bf1101c5714186094fa05d3277c5b2dbcec943dade361b269f 6.83kB / 6.83kB                                                                                                                          0.0s
 => => sha256:8b91b88d557765cd8c6802668755a3f6dc4337b6ce15a17e4857139e5fc964f3 27.14MB / 27.14MB                                                                                                                        6.2s
 => => sha256:824416e234237961c9c5d4f41dfe5b295a3c35a671ee52889bfb08d8e257ec4c 2.78MB / 2.78MB                                                                                                                          3.7s
 => => sha256:c87b3089b2ed5584d9a52ddf02017556958f287dd63945476fbcd191954e6faf 244B / 244B                                                                                                                              4.2s
 => => sha256:91bdacd599c69598dd6fbd7f97f7059b565f6f3015a04b6ab9e8db254a41652c 3.38MB / 3.38MB                                                                                                                          5.4s
 => => extracting sha256:8b91b88d557765cd8c6802668755a3f6dc4337b6ce15a17e4857139e5fc964f3                                                                                                                              19.2s
 => => extracting sha256:824416e234237961c9c5d4f41dfe5b295a3c35a671ee52889bfb08d8e257ec4c                                                                                                                               2.0s
 => => extracting sha256:482d64d97d4e63625e51301e23ca7ff526afaf40710da26704d9ce2e1a6168fa                                                                                                                               8.5s
 => => extracting sha256:c87b3089b2ed5584d9a52ddf02017556958f287dd63945476fbcd191954e6faf                                                                                                                               0.0s
 => => extracting sha256:91bdacd599c69598dd6fbd7f97f7059b565f6f3015a04b6ab9e8db254a41652c                                                                                                                               5.2s
 => [internal] load build context                                                                                                                                                                                       0.1s
 => => transferring context: 24.72kB                                                                                                                                                                                    0.0s
 => [2/9] WORKDIR /app                                                                                                                                                                                                  0.9s
 => [3/9] RUN apt-get update && apt-get install -y     ffmpeg     && rm -rf /var/lib/apt/lists/*                                                                                                                      144.4s
 => [4/9] COPY requirements.txt .                                                                                                                                                                                       0.6s 
 => [5/9] RUN pip install --no-cache-dir -r requirements.txt                                                                                                                                                           48.9s 
 => [6/9] COPY main.py .                                                                                                                                                                                                0.1s 
 => [7/9] COPY model/west.json ./model/                                                                                                                                                                                 0.0s 
 => [8/9] COPY settings/config.json ./settings/                                                                                                                                                                         0.1s
 => [9/9] COPY settings/fixed.json ./settings/                                                                                                                                                                          0.1s
 => exporting to image                                                                                                                                                                                                  3.6s
 => => exporting layers                                                                                                                                                                                                 3.6s
 => => writing image sha256:fbd32a4159a453a2237b00378a388536419813c33eb3f99676d49cc7498184a4                                                                                                                            0.0s
 => => naming to docker.io/library/west-ai                                                                                                                                                                              0.0s
```

</details>

### Step2: Docker Run

```
docker run west-ai
```

## Support

If you would like to support me, it would be my pleasure!

```
yblockchain.eth
```
