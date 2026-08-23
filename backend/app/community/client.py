"""컴프야V26 공식 커뮤니티(cpbv-community.com2us.com)에서 진행 중 이벤트/쿠폰 목록을 가져온다.

- 이벤트 목록: "진행 중 이벤트" 게시판(idx=6)의 공개 목록 API. 사이트가 클라이언트 JS에서
  호출하는 것과 동일한 공개 엔드포인트이며 로그인/인증이 필요하지 않다.
- 쿠폰 목록: 같은 게시판에 상단 고정(운영자 top)된 "※...쿠폰 모아보기!※" 게시글 본문의
  표를 파싱한다. 고정글 idx는 새 공지로 교체될 수 있어 제목으로 매번 찾는다.
"""
import httpx
from bs4 import BeautifulSoup

COMMUNITY_BASE = "https://cpbv-community.com2us.com"
EVENTS_BOARD_IDX = "6"
COUPON_POST_TITLE_HINT = "쿠폰 모아보기"


class CommunityFetchError(Exception):
    pass


async def _fetch_board_page(page_size: int = 20) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{COMMUNITY_BASE}/board/list/getBoardContents",
            data={
                "e_type": "board1",
                "idx": EVENTS_BOARD_IDX,
                "header": "",
                "lang": "ko",
                "selectType": "1",
                "page_size": str(page_size),
                "page_num": "1",
                "is_mobile": "N",
                "viewChk": "",
            },
        )
    data = resp.json()
    if data.get("ret_code") != 100:
        raise CommunityFetchError(f"게시판 조회 실패: {data}")
    return data


async def fetch_ongoing_events(limit: int = 10) -> list[dict]:
    data = await _fetch_board_page(page_size=limit)
    return [
        {
            "title": item["title"],
            "url": f"{COMMUNITY_BASE}/board/{EVENTS_BOARD_IDX}/{item['idx']}",
            "regdate": item["regdate"],
        }
        for item in data.get("data", [])[:limit]
    ]


async def fetch_coupons() -> list[dict]:
    data = await _fetch_board_page()
    post = next(
        (t for t in data.get("top_data", []) if COUPON_POST_TITLE_HINT in t.get("title", "")),
        None,
    )
    if post is None:
        raise CommunityFetchError("쿠폰 모아보기 고정 게시글을 찾지 못했습니다")

    post_url = f"{COMMUNITY_BASE}/board/{EVENTS_BOARD_IDX}/{post['idx']}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(post_url)

    soup = BeautifulSoup(resp.text, "html.parser")
    content = soup.select_one(".content")
    table = content.find("table") if content else None
    if table is None:
        raise CommunityFetchError("쿠폰 표를 찾지 못했습니다")

    coupons = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        # 표 상단에 배너/헤더 행이 섞여있어 NO 컬럼이 숫자인 행만 데이터로 인정한다.
        if len(cells) < 4 or not cells[0].get_text(strip=True).isdigit():
            continue
        code = cells[1].get_text(strip=True)
        if not code:
            continue
        link_el = cells[4].find("a") if len(cells) > 4 else None
        coupons.append(
            {
                "code": code,
                "reward": cells[2].get_text(strip=True, separator="\n"),
                "period": cells[3].get_text(strip=True, separator=" "),
                "url": link_el["href"] if link_el else None,
            }
        )

    return coupons
