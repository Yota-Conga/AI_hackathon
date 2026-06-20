from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ゲームデータ（固定）
GAME_DATA = {
    "player": {
        "name": "レイ・クロウ（あなた）",
        "color": "黒のパーカー"
    },
    "suspects": [
        {
            "id": "suspect_a",
            "name": "桐島 誠",
            "color": "グレーのスーツ",
            "morning": "自宅で一人で過ごしていた",
            "noon": "駅前のカフェでコーヒーを飲んでいた",
            "night": "帰宅後すぐに就寝した"
        },
        {
            "id": "suspect_b",
            "name": "月岡 ルミ",
            "color": "赤いコート",
            "morning": "ジムでトレーニングしていた",
            "noon": "友人と昼食をとっていた（友人の証言あり）",
            "night": "被害者のマンション近くを歩いていた（防犯カメラ映像あり）"
        },
        {
            "id": "suspect_c",
            "name": "藤波 ケンジ",
            "color": "紺のジャケット",
            "morning": "会社に出勤していた（同僚複数名が証言）",
            "noon": "社内会議に出席していた（議事録あり）",
            "night": "残業後に帰宅した（退勤記録あり）"
        }
    ],
    "documents": [
        {
            "id": "doc_witness",
            "title": "目撃者証言",
            "icon": "👁",
            "content": [
                {"id": "w1", "text": "午後11時頃、黒いパーカーを着た人物が被害者宅へ入るのを目撃した。", "editable": False},
                {"id": "w2", "text": "その人物は", "editable": False},
                {"id": "w2e", "text": "黒いパーカー", "editable": True, "max_chars": 10},
                {"id": "w2b", "text": "を着ており、身長は170cm前後だった。", "editable": False},
                {"id": "w3", "text": "目撃した時刻は", "editable": False},
                {"id": "w3e", "text": "午後11時00分", "editable": True, "max_chars": 10},
                {"id": "w3b", "text": "頃であった。", "editable": False}
            ],
            "total_char_limit": 20
        },
        {
            "id": "doc_forensic",
            "title": "鑑識レポート",
            "icon": "🔬",
            "content": [
                {"id": "f1", "text": "現場に残された毛髪のDNA解析を行った結果、", "editable": False},
                {"id": "f1e", "text": "データベースに一致なし", "editable": True, "max_chars": 15},
                {"id": "f1b", "text": "であった。", "editable": False},
                {"id": "f2", "text": "凶器に残された指紋は", "editable": False},
                {"id": "f2e", "text": "部分的な一致が確認された", "editable": True, "max_chars": 15},
                {"id": "f2b", "text": "。解析精度：87%。", "editable": False},
                {"id": "f3", "text": "現場に残された足跡のサイズは26.5cmであり、", "editable": False},
                {"id": "f3e", "text": "桐島 誠", "editable": True, "max_chars": 8},
                {"id": "f3b", "text": "の靴のサイズと一致した。", "editable": False}
            ],
            "total_char_limit": 25
        },
        {
            "id": "doc_timeline",
            "title": "行動記録",
            "icon": "📋",
            "content": [
                {"id": "t1", "text": "被害者と最後に連絡を取った人物：", "editable": False},
                {"id": "t1e", "text": "レイ・クロウ（容疑者外）", "editable": True, "max_chars": 12},
                {"id": "t1b", "text": "（午後9時、通話記録より）", "editable": False},
                {"id": "t2", "text": "事件当夜、被害者宅の近くで目撃された人物：", "editable": False},
                {"id": "t2e", "text": "月岡 ルミ", "editable": True, "max_chars": 8},
                {"id": "t2b", "text": "（防犯カメラ映像・午後10時45分）", "editable": False},
                {"id": "t3", "text": "被害者との金銭トラブルが確認された人物：", "editable": False},
                {"id": "t3e", "text": "藤波 ケンジ", "editable": True, "max_chars": 8},
                {"id": "t3b", "text": "（50万円の未回収債務）", "editable": False}
            ],
            "total_char_limit": 20
        }
    ],
    "true_culprit": "レイ・クロウ"
}

@app.route("/")
def index():
    return render_template("index.html", game_data=json.dumps(GAME_DATA, ensure_ascii=False))

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    tampered_docs = data.get("documents", [])

    # 改竄後の資料からプロンプトを構築
    doc_texts = []
    for doc in tampered_docs:
        doc_texts.append(f"【{doc['title']}】\n{doc['text']}")

    suspects_text = "\n".join([
        f"・{s['name']}（{s['color']}）：朝={s['morning']}、昼={s['noon']}、夜={s['night']}"
        for s in GAME_DATA["suspects"]
    ])

    prompt = f"""あなたは未来の警察組織が導入した犯罪捜査AIです。
与えられた資料のみを根拠として、最も合理的に犯人を特定してください。

【容疑者一覧】
{suspects_text}

【捜査資料】
{"".join(doc_texts)}

上記の資料を総合的に分析し、以下の形式で回答してください：

1. 各容疑者の疑惑度評価（根拠を資料から引用して説明）
2. 最終結論：犯人は「（容疑者名）」である
3. 判定理由（2〜3文で簡潔に）

重要：資料に記載のない推測は行わず、必ず資料の記述のみを根拠にしてください。"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content(prompt)
        result_text = response.text

        # 犯人名を抽出（簡易判定）
        culprit = None
        for suspect in GAME_DATA["suspects"]:
            if suspect["name"] in result_text:
                # 最終結論の行から犯人を探す
                for line in result_text.split("\n"):
                    if "最終結論" in line or "犯人は" in line:
                        if suspect["name"] in line:
                            culprit = suspect["name"]
                            break
                if culprit:
                    break

        # フォールバック：最後に登場する容疑者名
        if not culprit:
            last_pos = -1
            for suspect in GAME_DATA["suspects"]:
                pos = result_text.rfind(suspect["name"])
                if pos > last_pos:
                    last_pos = pos
                    culprit = suspect["name"]

        player_cleared = culprit != GAME_DATA["true_culprit"]

        return jsonify({
            "success": True,
            "analysis": result_text,
            "culprit": culprit,
            "player_cleared": player_cleared
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)