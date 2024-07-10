# 더치 Dutch
앱 하나로 복잡하고 귀찮았던 정산을 한번에 도와주는 앱입니다.

## Team
- 안지형 : 프론트엔드, 디자이너
- 박종민 : 백엔드



## Tech Stack

- **Frontend** : Java
- **Backend(server)** : FastAPI
- **Database** : MongoDB
- **IDE** : Android Studio, VSCode



## Details


### Tab1 : Friends

친구와 정산관계를 보여주는 탭

- 친구와 아직 정산되지 않은 목록들을 간단하게 정리하여 보여줍니다.
  - 채무 관계가 간단하게 정리되어 있습니다.
- 해당 정산 목록에 들어가서 정산하기 기능을 통해 목록을 없앨 수 있습니다.

<시연영상 및 사진>

### Tab2 : Group

내가 속해있는 그룹을 보여주고, 그룹 안에서 생긴 채무관계를 정리해서 보여주는 탭

- 내가 속해 있는 그룹들을 리스트로 보여줍니다.
- 그룹에 들어가면 지금까지의 그룹의 계산 내역을 보여줍니다.
- 그룹 내에서 복잡했던 채무관계를 간단하게 정리해주는 기능을 통해 정산을 쉽게 도와줍니다.

<시연 영상 및 사진>

### Tab3 : Profile

연동된 카카오톡 프로필과 닉네임, 내 소비내역 차트를 보여주는 탭

- 카카오톡에서 불러온 프로필 사진과 닉네임을 보여줍니다.
- 내 소비내역을 카테고리별로 정리하여 차트로 보여줍니다.

<시연 영상 및 사진>


# MongoDB with FastAPI

This is a small sample project demonstrating how to build an API with [MongoDB](https://developer.mongodb.com/) and [FastAPI](https://fastapi.tiangolo.com/).
It was written to accompany a [blog post](https://developer.mongodb.com/quickstart/python-quickstart-fastapi/) - you should go read it!

If you want to fastrack your project even further, check out the [MongoDB FastAPI app generator](https://github.com/mongodb-labs/full-stack-fastapi-mongodb) and eliminate much of the boilerplate of getting started.

## TL;DR

If you really don't want to read the [blog post](https://developer.mongodb.com/quickstart/python-quickstart-fastapi/) and want to get up and running,
activate your Python virtualenv, and then run the following from your terminal (edit the `MONGODB_URL` first!):

```bash
# Install the requirements:
pip install -r requirements.txt

# Configure the location of your MongoDB database:
export MONGODB_URL="mongodb+srv://<username>:<password>@<url>/<db>?retryWrites=true&w=majority"

# Start the service:
uvicorn app:app --reload
```

(Check out [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) if you need a MongoDB database.)

Now you can load http://localhost:8000/docs in your browser ... but there won't be much to see until you've inserted some data.

If you have any questions or suggestions, check out the [MongoDB Community Forums](https://developer.mongodb.com/community/forums/)!
