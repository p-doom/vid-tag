# ⚫ vid-tag

A minimalist implementation of a video labeling interface. We internally use this tool to annotate videos for cleanliness in order to train a data filtering  model (cf. [Video Pre-training](https://arxiv.org/abs/2206.11795), [Genie](https://arxiv.org/abs/2402.15391)).

## Usage

![vid-tag interface](https://raw.githubusercontent.com/p-doom/vid-tag/main/img/preview.gif)


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

You can annotate by clicking on the tags or by using the provided keybindings (number keys by default).

## Annotation database
vid-tag saves your annotations in a lightweight sqlite3 database with the following table schema:

```
| id | filepath | filename | is_annotated | tags |
```