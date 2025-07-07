
from gtts import gTTS

# Define the script to be narrated
script = """
So, Ava Sharma—aka @AuthenticAva—just dropped a blog post about her ‘humble beginnings.’
She says she grew up poor, moved constantly, and worked three jobs to survive.
But Reddit wasn’t buying it.
One user dug deep—and found receipts.
Ava actually went to a $28,000-a-year private school. Her family owns a $1.4 million home in Westport, Connecticut.
Her first job? Not a diner waitress—she interned at her dad’s PR firm.
And those college loans? Turns out she had a full merit scholarship at NYU.
The post went viral. TikTok exploded. Brand deals? On pause.
Ava’s image of ‘authenticity’? Shattered.
So… was it all a lie? Or just a carefully curated version of the truth?
You decide.
"""

# Generate the audio using gTTS
tts = gTTS(text=script, lang='en', slow=False)
tts.save("ava_sharma_expose.mp3")

print("Audio file 'ava_sharma_expose.mp3' has been generated.")
