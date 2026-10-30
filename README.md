# 우리집 난방비 비교

작년 겨울과 올겨울 가스 난방비를 비교하는 페이지입니다. GitHub Pages로 띄워서 휴대폰에서 로그인 없이 링크로 엽니다.

- 기상청 일평균기온: GitHub Actions가 매일 새벽 자동으로 받아 `data/kma.json`을 갱신
- 계량기 기록: 페이지에서 입력하면 `data/readings.json`에 바로 커밋
- 설정(지역, 운전 방식, 보일러): `data/settings.json`

## 폴더 구성

```
index.html                     페이지
data/kma.json                  기상청 관측소별 일평균기온 (2025-10-01부터)
data/readings.json             가스 계량기 기록
data/settings.json             지역·운전 설정·보일러
scripts/update_kma.py          기상청 기온 갱신 스크립트 (표준 라이브러리만 사용)
.github/workflows/update-kma.yml  매일 00:41(한국시간) 자동 실행
```

## 처음 한 번 설정

0. **워크플로 파일 옮기기**: `setup/update-kma.yml`을 `.github/workflows/update-kma.yml`로 옮깁니다(폴더가 없으면 만듭니다). 그다음 `setup` 폴더는 지워도 됩니다.
1. **저장소 만들기**: GitHub에서 새 저장소 `home-heating`을 만듭니다(Public). README는 추가하지 않습니다.
2. **올리기**: VS Code에서 이 폴더를 열고 소스 제어 → 저장소 초기화 → 커밋 → 브랜치 게시. 또는 터미널에서
   ```
   git init -b main
   git add .
   git commit -m "처음 올림"
   git remote add origin https://github.com/<계정>/home-heating.git
   git push -u origin main
   ```
3. **Pages 켜기**: 저장소 Settings → Pages → Source를 `Deploy from a branch`, Branch를 `main` / `/ (root)`로 저장.
   1~2분 뒤 `https://<계정>.github.io/home-heating/` 에서 열립니다.
4. **Actions 쓰기 권한**: Settings → Actions → General → Workflow permissions에서 `Read and write permissions` 선택 후 저장.
   Actions 탭 → `기상청 기온 갱신` → `Run workflow`로 한 번 돌려서 초록색이 뜨는지 확인합니다.
5. **기록용 토큰 만들기**: GitHub 오른쪽 위 프로필 → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new token
   - Repository access: `Only select repositories` → `home-heating`만 선택
   - Permissions → Repository permissions → **Contents: Read and write** (나머지는 그대로)
   - Expiration: 1년
6. **휴대폰에서**: 페이지 링크를 열고 ‘검침 기록’ 탭 → ‘저장 권한 설정’에 토큰을 붙여 넣고 ‘이 기기에 저장’. 브라우저 공유 메뉴에서 ‘홈 화면에 추가’.
   PC 등 다른 기기도 같은 토큰을 한 번씩 넣으면 됩니다.

## 알아둘 점

- **공개 저장소**: 무료 GitHub Pages는 공개 저장소에서만 동작하므로 계량값과 설정이 공개됩니다. 주소나 이름 같은 개인정보는 넣지 마세요.
- **토큰**: 이 저장소의 파일만 고칠 수 있는 토큰입니다. 휴대폰을 잃어버리면 GitHub에서 토큰을 삭제하면 됩니다.
- **기온 자동 갱신이 실패할 때**: 기상청 사이트가 해외 서버(GitHub Actions)의 접속을 막으면 Actions가 빨간색으로 실패합니다.
  그때는 PC에서 `python scripts/update_kma.py`를 실행하고 커밋·푸시하면 같은 결과가 됩니다.
- **페이지 반영 시간**: 기록은 즉시 저장되고 화면에도 바로 반영됩니다. 다른 기기에서는 새로고침하면 보입니다.

## 계산 방법

PRISM(Princeton Scorekeeping Method) 난방전용 change-point 회귀로 집의 난방 특성(난방 필요 외기온도 τ, 열손실 β, 기본 사용량 α)을 작년 검침값에서 학습하고, 실내온도·난방수 온도(보일러 효율)를 바꿨을 때의 사용량을 계산합니다.
근거: M. F. Fels, “PRISM: An Introduction”, *Energy and Buildings* 9(1–2), 1986.
