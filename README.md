# 컴프야v26 디스코드 인증/리더보드 봇

디스코드 서버의 기존 규칙 메시지에 반응(체크)하고, Hive 계정으로 인증한 멤버만 리더보드를 볼 수 있는 디스코드 앱.

- `discord-bot/` — Node.js(discord.js) 슬래시 커맨드/버튼 UI
- `backend/` — Python(FastAPI) Hive 인증, DB, 게임데이터, 역할 부여 담당

두 서비스는 내부 HTTP API(`X-Internal-Key` 헤더)로 통신한다. 전체 흐름은 [plan](.) 참고.

## 1. 라즈베리파이 배포 (Docker Compose)

```bash
git clone https://github.com/gunobo/cpbv26-discord-bot.git
cd cpbv26-discord-bot

cp backend/.env.example backend/.env
cp discord-bot/.env.example discord-bot/.env
# backend/.env, discord-bot/.env 채우기 (DISCORD_TOKEN 등)
# discord-bot/.env의 BACKEND_URL은 http://backend:8000 으로 설정 (compose 서비스명)

docker compose up -d --build
```

슬래시 커맨드(/인증, /리더보드, /스탯설정, /구단역할)는 최초 1회만 등록하면 된다:

```bash
docker compose run --rm discord-bot node deploy-commands.js
```

로그 확인: `docker compose logs -f`, 재배포: `git pull && docker compose up -d --build`.
DB(`app.db`)는 `backend_data` 볼륨에 저장되어 컨테이너를 재생성해도 유지된다.

## 2. 로컬 개발 (Docker 없이, 선택)

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

```bash
# discord-bot (다른 터미널)
cd discord-bot
npm install
cp .env.example .env
npm run deploy-commands
npm run dev
```

기본값은 `HIVE_MOCK_MODE=true` — 실제 Hive 서버 없이 인증 플로우 전체를 테스트할 수 있다.

## 3. 사용 흐름

1. 서버에 이미 있는 규칙 메시지에 `RULES_EMOJI`로 반응(체크)
2. (운영자, 최초 1회) `/구단역할 설정 구단:두산 베어스 역할:@두산팬` 으로 구단별 역할 매핑 등록
3. `/인증` → 규칙 메시지 반응 여부 자동 확인 → "Hive로 인증하기" 링크 제공
4. 링크 클릭 → (모킹 모드에서는 자동으로) 인증 완료 페이지 도달
5. 봇이 자동으로 `VERIFIED_ROLE_ID` 역할 부여 + (팀 정보가 있으면) 구단 역할 부여
6. 운영자가 `/스탯설정 @유저 팀 오버롤` 로 팀/오버롤 수동 입력 (실 게임 데이터 API가 없는 동안의 임시 방법) — 이때도 구단 역할이 자동으로 부여/교체됨
7. 인증된 멤버는 `/리더보드` 로 오버롤 순위 확인 가능

## 실제 서비스 전환 시 해야 할 일

- **Hive 콘솔 키**: `appid`/`gindex`/`hive_certification_key` 발급받아 `backend/.env`에 채우고 `HIVE_MOCK_MODE=false`로 변경. `HIVE_REDIRECT_URL`을 Hive 콘솔에 등록한 값과 정확히 일치시켜야 한다.
- **호스팅**: `WEB_BASE_URL`/`HIVE_REDIRECT_URL`은 공인 HTTPS 도메인이어야 한다 (로컬 개발 중에는 mock 모드로 충분).
- **게임 데이터 API**: 컴프야v26 팀 정보/오버롤을 조회할 수 있는 공식 공개 API는 없다(확인 완료). 컴투스로부터 비공개 API를 받으면 `backend/app/gamedata/provider.py`의 `GameDataProvider`를 구현한 새 클래스를 만들어 `backend/app/routers/verify.py`의 `game_data_provider` 인스턴스만 교체하면 된다.
- **역할 순서**: 봇의 역할이 `VERIFIED_ROLE_ID`와 `/구단역할`로 등록한 모든 역할보다 서버 역할 목록에서 위에 있어야 한다. 아래에 있으면 역할 부여가 403 에러로 실패한다.
