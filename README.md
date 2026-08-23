# 컴프야v26 디스코드 인증/리더보드 봇

디스코드 서버의 기존 규칙 메시지에 반응(체크)하고, 인증한 멤버만 리더보드를 볼 수 있는 디스코드 앱.

Hive 콘솔 키가 아직 없어도 바로 운영할 수 있도록, `/인증`의 동작 방식이 백엔드 설정에 따라 자동으로 바뀐다:
- **Hive 미연동**(`HIVE_MOCK_MODE=true` 이거나 `HIVE_APPID`/`HIVE_GINDEX`/`HIVE_CERTIFICATION_KEY` 중 하나라도 비어있음): 규칙 메시지 반응 확인만으로 즉시 인증 완료 처리 (`구단역할 설정`, `구단역할 목록`, `/스탯설정`은 이 상태에서도 그대로 사용 가능)
- **Hive 연동됨**(모킹 꺼짐 + 키 전부 채워짐): 기존처럼 Hive 로그인 링크를 제공하고 PlayerID까지 확인
- 현재 상태는 운영자가 `/하이브상태`로 언제든 확인 가능. 나중에 키를 채우고 `HIVE_MOCK_MODE=false`로 바꾸면 재기동만으로 자동 전환되며, 기존에 "규칙 확인"으로 인증된 유저도 다시 `/인증`을 실행하면 Hive 인증으로 업그레이드된다.

- `discord-bot/` — Node.js(discord.js) 슬래시 커맨드/버튼 UI
- `backend/` — Python(FastAPI) Hive 인증, DB, 게임데이터, 역할 부여 담당

두 서비스는 내부 HTTP API(`X-Internal-Key` 헤더)로 통신한다. 전체 흐름은 [plan](.) 참고.

## 1. 라즈베리파이 배포 (Docker Compose)

```bash
git clone https://github.com/gunobo/cpbv26-discord-bot.git
cd cpbv26-discord-bot

cp backend/.env.example backend/.env
cp discord-bot/.env.example discord-bot/.env
cp .env.example .env
# backend/.env, discord-bot/.env, .env 채우기 (DISCORD_TOKEN 등)
# discord-bot/.env의 BACKEND_URL은 http://backend:8000 으로 설정 (compose 서비스명)

docker compose up -d --build
```

### 공인 도메인 연결 (Cloudflare Tunnel)

인증 링크를 실제로 다른 사람이 클릭하려면 `localhost`가 아닌 외부에서 접근 가능한 주소가 필요하다. `docker-compose.yml`에 `cloudflared` 서비스가 이미 포함되어 있으니, 아래 절차로 연결한다.

1. [Cloudflare Zero Trust 대시보드](https://one.dash.cloudflare.com/) → **Networks → Tunnels → Create a tunnel**
2. Connector 종류로 **Docker** 선택 → 터널 이름 입력(예: `cpbv26-discord-bot`) → 생성 화면에 나오는 `--token` 뒤의 긴 문자열을 복사
3. 루트 `.env`의 `CLOUDFLARE_TUNNEL_TOKEN`에 붙여넣기
4. 같은 화면(또는 터널 상세 → Public Hostname)에서 **Public Hostname** 추가:
   - Subdomain/Domain: 원하는 서브도메인 (예: `cpbv26.내도메인.com`)
   - Service: `HTTP` / URL: `backend:8000` (compose 서비스명 — cloudflared 컨테이너가 같은 네트워크에 있어서 가능)
5. `backend/.env`의 `WEB_BASE_URL`, `HIVE_REDIRECT_URL`을 그 도메인(`https://cpbv26.내도메인.com`, `.../verify/callback`)으로 변경
6. `docker compose up -d --build` 로 재기동

이후 Hive 콘솔 키를 발급받으면 `HIVE_REDIRECT_URL`을 Hive 콘솔에도 **정확히 동일한 값으로** 등록해야 한다.

슬래시 커맨드(/인증, /리더보드, /스탯설정, /구단역할, /내정보, /인증해제, /하이브상태)는 최초 1회만 등록하면 된다:

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
3. `/인증` → 규칙 메시지 반응 여부 자동 확인 후, Hive 연동 상태에 따라:
   - 미연동: 즉시 인증 완료 (Verified 역할 바로 부여)
   - 연동됨: "Hive로 인증하기" 링크 제공 → 로그인 완료 시 Verified 역할 부여
4. 봇이 자동으로 (팀 정보가 있으면) 구단 역할도 함께 부여
5. 운영자가 `/스탯설정 @유저 팀 오버롤` 로 팀/오버롤 수동 입력 (실 게임 데이터 API가 없는 동안의 임시 방법, Hive 연동 여부와 무관하게 항상 사용 가능) — 이때도 구단 역할이 자동으로 부여/교체됨
6. 인증된 멤버는 `/리더보드` 로 오버롤 순위 확인 (구단 필터, 페이지네이션 지원)
7. 유저 본인은 `/내정보`, 운영자는 `/하이브상태`·`/인증해제`로 상태 확인/관리

## 실제 서비스 전환 시 해야 할 일

- **Hive 콘솔 키**: `appid`/`gindex`/`hive_certification_key` 발급받아 `backend/.env`에 채우고 `HIVE_MOCK_MODE=false`로 변경. `HIVE_REDIRECT_URL`을 Hive 콘솔에 등록한 값과 정확히 일치시켜야 한다.
- **호스팅**: `WEB_BASE_URL`/`HIVE_REDIRECT_URL`은 공인 HTTPS 도메인이어야 한다 (로컬 개발 중에는 mock 모드로 충분).
- **게임 데이터 API**: 컴프야v26 팀 정보/오버롤을 조회할 수 있는 공식 공개 API는 없다(확인 완료). 컴투스로부터 비공개 API를 받으면 `backend/app/gamedata/provider.py`의 `GameDataProvider`를 구현한 새 클래스를 만들어 `backend/app/routers/verify.py`의 `game_data_provider` 인스턴스만 교체하면 된다.
- **역할 순서**: 봇의 역할이 `VERIFIED_ROLE_ID`와 `/구단역할`로 등록한 모든 역할보다 서버 역할 목록에서 위에 있어야 한다. 아래에 있으면 역할 부여가 403 에러로 실패한다.
