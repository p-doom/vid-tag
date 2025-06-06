# ⚫ vid-tag

A minimalist implementation of a video labeling interface. We internally use this tool to annotate videos for cleanliness in order to train a data filtering  model (cf. [Video Pre-training](https://arxiv.org/abs/2206.11795), [Genie](https://arxiv.org/abs/2402.15391)).

## Usage
Install the requirements with:
```bash
pip install -r requirements.txt
```

Next, set your video folder, a database URL, and the tags of your choice in a `.env` file:
```bash
# ./.env
VIDEO_FOLDER_PATH="./data"
DATABASE_URL="sqlite:///./vid_tag.db"
PREDEFINED_TAGS='["TagA", "TagB", "TagC", "Needs Review"]' 
```

Finally, simply run the webserver:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```