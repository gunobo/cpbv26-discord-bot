# 컴프야v26 디스코드 인증/리더보드 봇

디스코드 서버 규칙에 동의하고 Hive 계정으로 인증한 멤버만 리더보드를 볼 수 있는 디스코드 앱.

- `discord-bot/` — Node.js(discord.js) 슬래시 커맨드/버튼 UI
- `backend/` — Python(FastAPI) Hive 인증, DB, 게임데이터, 역할 부여 담당

두 서비스는 내부 HTTP API(`X-Internal-Key` 헤더)로 통신한다. 전체 흐름은 [plan](.) 참고.

## 1. backend 실행

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

기본값은 `HIVE_MOCK_MODE=true` — 실제 Hive 서버 없이 인증 플로우 전체를 테스트할 수 있다.

## 2. discord-bot 실행

```bash
cd discord-bot
npm install
cp .env.example .env   # DISCORD_TOKEN, DISCORD_CLIENT_ID, DISCORD_GUILD_ID, VERIFIED_ROLE_ID,
                        # INTERNAL_API_KEY(backend/.env와 동일 값) 채우기
npm run deploy-commands # 슬래시 커맨드(/인증, /리더보드, /스탯설정)를 길드에 등록
npm run dev
```

## 3. 사용 흐름

1. `/인증` → 서버 규칙 확인 → "규칙에 동의합니다" 클릭
2. "Hive로 인증하기" 링크 클릭 → (모킹 모드에서는 자동으로) 인증 완료 페이지 도달
3. 봇이 자동으로 `VERIFIED_ROLE_ID` 역할 부여
4. 운영자가 `/스탯설정 @유저 팀 오버롤` 로 팀/오버롤 수동 입력 (실 게임 데이터 API가 없는 동안의 임시 방법)
5. 인증된 멤버는 `/리더보드` 로 오버롤 순위 확인 가능

## 실제 서비스 전환 시 해야 할 일

- **Hive 콘솔 키**: `appid`/`gindex`/`hive_certification_key` 발급받아 `backend/.env`에 채우고 `HIVE_MOCK_MODE=false`로 변경. `HIVE_REDIRECT_URL`을 Hive 콘솔에 등록한 값과 정확히 일치시켜야 한다.
- **호스팅**: `WEB_BASE_URL`/`HIVE_REDIRECT_URL`은 공인 HTTPS 도메인이어야 한다 (로컬 개발 중에는 mock 모드로 충분).
- **게임 데이터 API**: 컴프야v26 팀 정보/오버롤을 조회할 수 있는 공식 공개 API는 없다(확인 완료). 컴투스로부터 비공개 API를 받으면 `backend/app/gamedata/provider.py`의 `GameDataProvider`를 구현한 새 클래스를 만들어 `backend/app/routers/verify.py`의 `game_data_provider` 인스턴스만 교체하면 된다.
