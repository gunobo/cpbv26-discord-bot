"""컴프야V26 공식 커뮤니티(cpbv-community.com2us.com)의 "진행 중 이벤트" 게시판(board idx=6)을
공개 목록 API로 조회한다. 사이트가 클라이언트 JS에서 호출하는 것과 동일한 공개 엔드포인트이며
로그인/인증이 필요하지 않다."""
import httpx

COMMUNITY_BASE = "https://cpbv-community.com2us.com"
EVENTS_BOARD_IDX = "6"


class CommunityFetchError(Exception):
    pass


async def fetch_ongoing_events(limit: int = 10) -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{COMMUNITY_BASE}/board/list/getBoardContents",
            data={
                "e_type": "board1",
                "idx": EVENTS_BOARD_IDX,
                "header": "",
                "lang": "ko",
                "selectType": "1",
                "page_size": str(limit),
                "page_num": "1",
                "is_mobile": "N",
                "viewChk": "",
            },
        )
    data = resp.json()
    if data.get("ret_code") != 100:
        raise CommunityFetchError(f"이벤트 목록 조회 실패: {data}")

    return [
        {
            "title": item["title"],
            "url": f"{COMMUNITY_BASE}/board/{EVENTS_BOARD_IDX}/{item['idx']}",
            "regdate": item["regdate"],
        }
        for item in data.get("data", [])[:limit]
    ]
