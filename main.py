import discord
from discord.ext import commands
from discord import app_commands
import openai
import anthropic
import json
import re
import os
import io
import PyPDF2
import csv
import uuid
import base64
import asyncio
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import requests

with open('settings/config.json', 'r') as f:
    config = json.load(f)

DISCORD_TOKEN = config['DISCORD_TOKEN']
OPENAI_API_KEY = config['OPENAI_API_KEY']
ELEVENLABS_API_KEY = config['ELEVENLABS_API_KEY']
VOICE_ID = config['VOICE_ID']
MAX_TTS_LENGTH = config['MAX_TTS_LENGTH']
LISTENING_STATUS = config['LISTENING_STATUS']
ANTHROPIC_API_KEY = config['ANTHROPIC_API_KEY']

#標準モデルのグローバル変数
CURRENT_AI = "ChatGPT"
CURRENT_MODEL = "gpt-4"

EMBED_COLOR_NORMAL = 0x00bfff
EMBED_COLOR_ERROR = 0xFF0000

openai.api_key = OPENAI_API_KEY
anthropic_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

with open('model/west.json', 'r') as f:
    data = json.load(f)
training_data = "\n".join(data['training_data'])

with open('settings/fixed.json', 'r') as f:
    fix_reading_data = json.load(f)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

conversation_history = {}

#モデル選択
class ModelChoices(discord.Enum):
    GPT_4 = "gpt-4"
    GPT_4O = "gpt-4o"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20240620"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"

CHATGPT_MODELS = [ModelChoices.GPT_4, ModelChoices.GPT_4O, ModelChoices.GPT_3_5_TURBO]
CLAUDE_MODELS = [ModelChoices.CLAUDE_3_5_SONNET, ModelChoices.CLAUDE_3_OPUS, ModelChoices.CLAUDE_3_SONNET, ModelChoices.CLAUDE_3_HAIKU]

def apply_fix_reading(text: str) -> str:
    for key, value in fix_reading_data.items():
        text = text.replace(key, value)
    return text

def extract_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            p = parse_qs(parsed_url.query)
            return p['v'][0]
        if parsed_url.path[:7] == '/embed/':
            return parsed_url.path.split('/')[2]
        if parsed_url.path[:3] == '/v/':
            return parsed_url.path.split('/')[2]
    return None

#モデル変数アップデート
def update_current_model(ai: str, model: str):
    global CURRENT_AI, CURRENT_MODEL
    CURRENT_AI = ai
    CURRENT_MODEL = model
    print(f"モデルが更新されました: {CURRENT_AI} ({CURRENT_MODEL})")

async def text_to_speech_file(text: str) -> str:
    url_pattern = re.compile(r'https?://\S+')
    
    try:
        text = url_pattern.sub('', text)
        text = apply_fix_reading(text)
        
        response = await asyncio.to_thread(
            eleven_client.text_to_speech.convert,
            voice_id=VOICE_ID,
            optimize_streaming_latency="0",
            output_format="mp3_22050_32",
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5, 
                similarity_boost=0.75,
                style=0.3,
                language="ja",
                use_speaker_boost=True,
            ),
        )
    except Exception as e:
        print(f"Error during text-to-speech conversion: {str(e)}")
        return None
    
    save_file_name = f"{uuid.uuid4()}.mp3"
    save_file_path = os.path.join(os.getcwd(), save_file_name)
    
    try:
        with open(save_file_path, "wb") as f:
            for chunk in response:
                if chunk:
                    f.write(chunk)
        print(f"{save_file_path}: A new audio file was saved successfully!")
        return save_file_path
    except Exception as e:
        print(f"Error while saving the audio file: {str(e)}")
        return None

async def get_video_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja', 'en'])
        return " ".join([entry['text'] for entry in transcript])
    except Exception as e:
        print(f"字幕の取得中にエラーが発生しました: {str(e)}")
        return None

async def get_video_title(video_id):
    try:
        url = f"https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(url)
        data = response.json()
        return data['title']
    except Exception as e:
        print(f"動画タイトルの取得中にエラーが発生しました: {str(e)}")
        return "YouTube動画"

async def summarize_video(text, custom_system_prompt=None):
    try:
        system_prompt = custom_system_prompt or "以下のテキスト(動画の字幕)を簡潔に要約してください。少し動画の趣旨や具体的に話している部分も説明してください。(動画構成など)"
        
        if CURRENT_AI == "ChatGPT":
            response = await openai.ChatCompletion.acreate(
                model=CURRENT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=4096,
                temperature=0.7,
            )
            return response.choices[0].message.content
        elif CURRENT_AI == "Claude":
            response = await anthropic_client.messages.create(
                model=CURRENT_MODEL,
                max_tokens=4000,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": text}
                ]
            )
            return response.content[0].text
    except Exception as e:
        print(f"要約中にエラーが発生しました: {str(e)}")
        return None

async def read_file_content(attachment):
    content = ""
    if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        image_data = await attachment.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "この画像を詳細に説明してください。余計な説明は避け、画像の内容のみを簡潔に述べてください。"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=4096,
            )
            content = response.choices[0].message.content
        except Exception as e:
            print(f"Error during image recognition: {str(e)}")
            content = "画像の認識中にエラーが発生しました。"
    elif attachment.filename.endswith('.pdf'):
        pdf_content = await attachment.read()
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            content += page.extract_text() + "\n"
    elif attachment.filename.endswith('.txt'):
        content = (await attachment.read()).decode('utf-8')
    elif attachment.filename.endswith('.csv'):
        csv_content = (await attachment.read()).decode('utf-8')
        csv_reader = csv.reader(csv_content.splitlines())
        for row in csv_reader:
            content += ', '.join(row) + "\n"
    else:
        content = "Unsupported file type"
    return content

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=LISTENING_STATUS))
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.tree.command(name="change_model", description="使用するAIモデルを変更します。")
@app_commands.choices(ai=[
    app_commands.Choice(name="ChatGPT", value="ChatGPT"),
    app_commands.Choice(name="Claude", value="Claude")
])
@app_commands.choices(model=[
    app_commands.Choice(name=model.name, value=model.value) for model in ModelChoices
])
async def change_model(interaction: discord.Interaction, ai: str, model: str):
    if ai == "ChatGPT" and model not in [m.value for m in CHATGPT_MODELS]:
        embed = discord.Embed(description="選択されたモデルはChatGPTで利用できません。", color=EMBED_COLOR_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    elif ai == "Claude" and model not in [m.value for m in CLAUDE_MODELS]:
        embed = discord.Embed(description="選択されたモデルはClaudeで利用できません。", color=EMBED_COLOR_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    update_current_model(ai, model)
    embed = discord.Embed(description=f"AIモデルが{CURRENT_AI} ({CURRENT_MODEL})に変更されました。", color=EMBED_COLOR_NORMAL)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="current_model", description="現在使用中のAIモデルを表示します。")
async def show_current_model(interaction: discord.Interaction):
    embed = discord.Embed(description=f"現在使用中のAIモデル: {CURRENT_AI} ({CURRENT_MODEL})", color=EMBED_COLOR_NORMAL)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="summarize_youtube", description="YouTubeビデオの内容を要約します。オプションでシステムプロンプトを指定できます。")
async def summarize_youtube(interaction: discord.Interaction, url: str, system_prompt: str = None):
    await interaction.response.defer()

    video_id = extract_video_id(url)
    if not video_id:
        embed = discord.Embed(description="無効なYouTube URLです。", color=EMBED_COLOR_ERROR)
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    title = await get_video_title(video_id)
    transcript = await get_video_transcript(video_id)
    if not transcript:
        await interaction.followup.send("字幕を取得できませんでした。", ephemeral=True)
        return

    summary = await summarize_video(transcript, system_prompt)
    if not summary:
        await interaction.followup.send("要約を生成できませんでした。", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"『{title}』の要約",
        description=summary,
        color=EMBED_COLOR_NORMAL
    )
    embed.add_field(name="元の動画", value=url, inline=False)
    embed.add_field(name="使用したAIモデル", value=f"{CURRENT_AI} ({CURRENT_MODEL})", inline=False)
    if system_prompt:
        embed.add_field(name="使用したシステムプロンプト", value=system_prompt, inline=False)

    await interaction.followup.send(embed=embed)

    if interaction.guild.voice_client and interaction.guild.voice_client.is_connected():
        if len(summary) <= MAX_TTS_LENGTH:
            audio_file = await text_to_speech_file(summary)
            if audio_file:
                audio_source = discord.FFmpegPCMAudio(audio_file, options="-filter:a 'volume=1.5'")
                interaction.guild.voice_client.play(audio_source)
                while interaction.guild.voice_client.is_playing():
                    await asyncio.sleep(1)
                os.remove(audio_file)

@bot.tree.command(name="join", description="WestAIをボイスチャンネルに参加させます。")
async def join(interaction: discord.Interaction):
    if interaction.user.voice and interaction.user.voice.channel:
        channel = interaction.user.voice.channel
        await channel.connect()
        embed = discord.Embed(description="ボイスチャンネルに参加しました。", color=EMBED_COLOR_NORMAL)
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(description="ボイスチャンネルに参加してからコマンドを使用してください。", color=EMBED_COLOR_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="leave", description="WestAIをボイスチャンネルから退出させます。")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client and interaction.guild.voice_client.is_connected():
        await interaction.guild.voice_client.disconnect()
        embed = discord.Embed(description="ボイスチャンネルから退出しました。", color=EMBED_COLOR_NORMAL)
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(description="ボイスチャンネルに参加していません。", color=EMBED_COLOR_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="change_text", description="読み上げ文字数を変更します。")
async def change_text(interaction: discord.Interaction, length: int):
    global MAX_TTS_LENGTH
    if length > 0:
        MAX_TTS_LENGTH = length
        config['MAX_TTS_LENGTH'] = length
        with open('settings/config.json', 'w') as f:
            json.dump(config, f, indent=4)
        embed = discord.Embed(description=f"読み上げ文字数が{MAX_TTS_LENGTH}文字に変更されました。", color=EMBED_COLOR_NORMAL)
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(description="読み上げ文字数は正の整数で指定してください。", color=EMBED_COLOR_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="fix_reading", description="単語の読み方を修正します。")
async def fix_reading(interaction: discord.Interaction, word: str, reading: str):
    global fix_reading_data
    if word in fix_reading_data:
        old_reading = fix_reading_data[word]
        fix_reading_data[word] = reading
        with open('settings/fixed.json', 'w') as f:
            json.dump(fix_reading_data, f, ensure_ascii=False, indent=4)
        embed = discord.Embed(description=f"読み方の修正情報が更新されました。 {word}: {old_reading} -> {reading}", color=EMBED_COLOR_NORMAL)
    else:
        fix_reading_data[word] = reading
        with open('settings/fixed.json', 'w') as f:
            json.dump(fix_reading_data, f, ensure_ascii=False, indent=4)
        embed = discord.Embed(description=f"読み方の修正情報が追加されました。 {word} -> {reading}", color=EMBED_COLOR_NORMAL)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="fix_list", description="現在の読み方修正情報を表示します。")
async def fix_list(interaction: discord.Interaction):
    if len(fix_reading_data) > 0:
        embed = discord.Embed(title="現在のfix情報", color=EMBED_COLOR_NORMAL)
        for word, reading in fix_reading_data.items():
            embed.add_field(name=word, value=reading, inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(description="現在、fix情報はありません。", color=EMBED_COLOR_NORMAL)
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ask", description="BOTに質問します。添付ファイル (画像含む) の内容も考慮されます。テキストファイルとして保存することも可能。")
async def ask(interaction: discord.Interaction, question: str, attachment: discord.Attachment = None, save_as_text: bool = False):
    await interaction.response.defer()

    user_id = str(interaction.user.id)
    if user_id not in conversation_history:
        conversation_history[user_id] = [{"role": "system", "content": training_data}]

    if attachment:
        file_content = await read_file_content(attachment)
        if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            question = f"以下は添付された画像の説明です：\n\n{file_content}\n\nこの画像の内容を考慮して、次の質問に答えてください: {question}"
        else:
            question = f"以下の添付ファイルの内容を考慮して質問に答えてください：\n\n{file_content}\n\n質問: {question}"

    if save_as_text:
        question += "\n\nMarkdown形式で回答を作成してください。適切な見出しレベル(#, ##, ###など)を使用し、テキストの構造を整えてください。コードブロックや箇条書きなども適切に使用してください。また、不要な説明や前置きは省いて、質問への直接的な回答のみを含めてください。"

    conversation_history[user_id].append({"role": "user", "content": question})

    try:
        if CURRENT_AI == "ChatGPT":
            response = await openai.ChatCompletion.acreate(
                model=CURRENT_MODEL,
                messages=conversation_history[user_id],
                max_tokens=4096,
                temperature=0.7,
            )
            assistant_response = response.choices[0].message.content
        elif CURRENT_AI == "Claude":
            response = await anthropic_client.messages.create(
                model=CURRENT_MODEL,
                max_tokens=4000,
                temperature=0.7,
                system=conversation_history[user_id][0]["content"],
                messages=conversation_history[user_id][1:]
            )
            assistant_response = response.content[0].text
        
        conversation_history[user_id].append({"role": "assistant", "content": assistant_response})
        
        total_chars = len(assistant_response)
        
        embed = discord.Embed(
            description=assistant_response[:2000] + "..." if len(assistant_response) > 2000 else assistant_response,
            color=EMBED_COLOR_NORMAL
        )
        embed.set_footer(text=f"レスポンス文字数: {total_chars} | 使用モデル: {CURRENT_AI} ({CURRENT_MODEL})")
        
        if save_as_text:
            file_name = f"response_{uuid.uuid4()}.md"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(assistant_response)
            await interaction.followup.send(embed=embed, file=discord.File(file_name))
            os.remove(file_name)
        else:
            await interaction.followup.send(embed=embed)
        
        if interaction.guild.voice_client and interaction.guild.voice_client.is_connected():
            text_to_speech = re.sub(r'```.*?```', '', assistant_response, flags=re.DOTALL)
            if len(text_to_speech) <= MAX_TTS_LENGTH:
                audio_file = await text_to_speech_file(text_to_speech)
                if audio_file:
                    audio_source = discord.FFmpegPCMAudio(audio_file, options="-filter:a 'volume=1.5'")
                    interaction.guild.voice_client.play(audio_source)
                    while interaction.guild.voice_client.is_playing():
                        await asyncio.sleep(1)
                    os.remove(audio_file)
        else:
            print("Bot is not connected to a voice channel.")
    except Exception as e:
        error_embed = discord.Embed(description=f"エラーが発生しました: {str(e)}", color=EMBED_COLOR_ERROR)
        await interaction.followup.send(embed=error_embed, ephemeral=True)

@bot.tree.command(name="reset_conversation", description="会話履歴をリセットします。")
async def reset_conversation(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id in conversation_history:
        conversation_history[user_id] = [{"role": "system", "content": training_data}]
        embed = discord.Embed(description="会話履歴がリセットされました。", color=EMBED_COLOR_NORMAL)
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(description="リセットする会話履歴がありません。", color=EMBED_COLOR_NORMAL)
        await interaction.response.send_message(embed=embed)

bot.run(DISCORD_TOKEN)
