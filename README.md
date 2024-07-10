# MadCamp_Week2

# 프로젝트 이름

## Tech Stack

---

- **Frontend** : Java
- **Backend(server)** : FastAPI
- **Database** : MongoDB
- **IDE** : Android Studio, VSCode

## Details

---

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

---

## Installation

1. 레포지토리를 클론합니다:
    ```bash
    git clone https://github.com/yourusername/yourrepository.git
    ```
2. 필요한 종속성을 설치합니다:
    ```bash
    cd yourrepository
    pip install -r requirements.txt
    ```

## Usage

1. 백엔드 서버를 시작합니다:
    ```bash
    uvicorn main:app --reload
    ```
2. Android Studio를 사용하여 프론트엔드 애플리케이션을 실행합니다.

## Contributing

기여를 환영합니다! 개선 사항이 있으면 이슈를 등록하거나 풀 리퀘스트를 생성해 주세요.

## License

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참고하세요.
