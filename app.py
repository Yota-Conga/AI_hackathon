from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ゲームデータ
# 初期状態ではプレイヤー（レイ・クロウ）が犯人と特定されるように設計
# → 黒パーカー目撃、DNA一致、通話記録、足跡が全部プレイヤーを指している
GAME_DATA = {
    "player": {
        "name": "レイ・クロウ",
        "color": "黒のパーカー"
    },
    "suspects": [
        {
            "id": "suspect_a",
            "name": "桐島 誠",
            "color": "グレーのスーツ",
            "morning": "自宅で一人で過ごしていた（証人なし）",
            "noon": "駅前のカフェでコーヒーを飲んでいた",
            "night": "帰宅後すぐに就寝した（証人なし）"
        },
        {
            "id": "suspect_b",
            "name": "月岡 ルミ",
            "color": "赤いコート",
            "morning": "ジムでトレーニングしていた（スタッフ証言あり）",
            "noon": "友人と昼食をとっていた（友人の証言あり）",
            "night": "自宅で過ごしていた（家族の証言あり）"
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
            "title": "目撃者証言調書",
            "doc_number": "証言-2047-0312-01",
            "date": "2047年3月12日",
            "author": "捜査官 山田 一郎",
            "icon": "👁️",
            "content": [
                {"id": "w0", "text": "事件当夜（3月11日）午後11時頃、被害者宅付近にて不審な人物を目撃した。", "editable": False},
                {"id": "w1", "text": "その人物は", "editable": False},
                {"id": "w1e", "text": "黒いパーカー", "editable": True, "max_chars": 10},
                {"id": "w1b", "text": "を着用しており、身長170cm前後の細身の体型であった。", "editable": False},
                {"id": "w2", "text": "目撃時刻は", "editable": False},
                {"id": "w2e", "text": "午後11時00分", "editable": True, "max_chars": 10},
                {"id": "w2b", "text": "頃であり、人物は被害者宅の玄関ドアに向かって歩いて行った。", "editable": False},
                {"id": "w3", "text": "なお、目撃者は同日午前中に被害者と", "editable": False},
                {"id": "w3e", "text": "レイ・クロウ", "editable": True, "max_chars": 10},
                {"id": "w3b", "text": "が口論しているのも目撃していると述べた。", "editable": False}
            ],
            "total_char_limit": 20
        },
        {
            "id": "doc_forensic",
            "title": "鑑識科学捜査レポート",
            "doc_number": "鑑識-2047-0312-03",
            "date": "2047年3月12日",
            "author": "鑑識技官 佐藤 美咲",
            "icon": "🔬",
            "content": [
                {"id": "f0", "text": "犯行現場（被害者宅・居室）における鑑識調査の結果を以下に報告する。", "editable": False},
                {"id": "f1", "text": "【毛髪DNA】現場採取の毛髪をDNA解析した結果、", "editable": False},
                {"id": "f1e", "text": "レイ・クロウのDNAと一致", "editable": True, "max_chars": 15},
                {"id": "f1b", "text": "した（一致率99.7%）。", "editable": False},
                {"id": "f2", "text": "【指紋】凶器（刃物）に残された指紋について照合した結果、", "editable": False},
                {"id": "f2e", "text": "レイ・クロウの右手人差し指", "editable": True, "max_chars": 15},
                {"id": "f2b", "text": "の指紋と一致した（解析精度：94%）。", "editable": False},
                {"id": "f3", "text": "【足跡】現場に残された足跡（26.5cm）は、", "editable": False},
                {"id": "f3e", "text": "桐島 誠", "editable": True, "max_chars": 8},
                {"id": "f3b", "text": "の靴サイズと合致した。", "editable": False}
            ],
            "total_char_limit": 25
        },
        {
            "id": "doc_timeline",
            "title": "行動記録・通信履歴報告書",
            "doc_number": "記録-2047-0312-02",
            "date": "2047年3月12日",
            "author": "デジタル捜査班 中村 隆",
            "icon": "📋",
            "content": [
                {"id": "t0", "text": "事件当日（3月11日）の関係者の行動記録および通信履歴を以下に示す。", "editable": False},
                {"id": "t1", "text": "【通話記録】被害者が最後に通話した相手は", "editable": False},
                {"id": "t1e", "text": "レイ・クロウ", "editable": True, "max_chars": 12},
                {"id": "t1b", "text": "であり、通話時刻は午後9時14分（通話時間8分）であった。", "editable": False},
                {"id": "t2", "text": "【位置情報】午後10時45分、被害者宅から50m以内に携帯端末の位置情報が記録された人物：", "editable": False},
                {"id": "t2e", "text": "レイ・クロウ", "editable": True, "max_chars": 8},
                {"id": "t2b", "text": "（端末ID照合済み）。", "editable": False},
                {"id": "t3", "text": "【動機】被害者との金銭トラブルが記録されている人物：", "editable": False},
                {"id": "t3e", "text": "レイ・クロウ", "editable": True, "max_chars": 8},
                {"id": "t3b", "text": "（被害者より150万円の債務、返済期限超過）。", "editable": False}
            ],
            "total_char_limit": 20
        }
    ],
    "true_culprit": "レイ・クロウ",
    "model_answer": {
        "target": "桐島 誠",
        "steps": [
            {
                "doc": "鑑識科学捜査レポート",
                "field": "足跡の一致人物（f3e）",
                "from": "桐島 誠",
                "to": "月岡 ルミ または 藤波 ケンジ",
                "reason": "足跡は現場の物理証拠。これを別人名に変えると、その容疑者が現場にいた証拠になる。"
            },
            {
                "doc": "目撃者証言調書",
                "field": "口論目撃の人物名（w3e）",
                "from": "レイ・クロウ",
                "to": "桐島 誠",
                "reason": "被害者と口論していたことは強い動機の証拠。これを桐島に変えると動機が桐島に移る。"
            },
            {
                "doc": "行動記録・通信履歴報告書",
                "field": "金銭トラブルの人物名（t3e）",
                "from": "レイ・クロウ",
                "to": "桐島 誠",
                "reason": "金銭トラブルは最大の動機。これを桐島に変えると、桐島に明確な動機ができる。"
            }
        ],
        "summary": "DNAや通話記録など、消しにくい証拠はそのままに、足跡・口論・金銭トラブルを桐島 誠に向け変える。アリバイのない桐島に動機と物証が重なり、AIは桐島を犯人と判定する。"
    }
}

@app.route("/")
def index():
    return render_template("index.html", game_data=GAME_DATA)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    tampered_docs = data.get("documents", [])

    doc_texts = []
    for doc in tampered_docs:
        doc_texts.append(f"\n【{doc['title']}】\n{doc['text']}\n")

    suspects_text = "\n".join([
        f"・{s['name']}（服装：{s['color']}）\n  朝：{s['morning']}\n  昼：{s['noon']}\n  夜：{s['night']}"
        for s in GAME_DATA["suspects"]
    ])

    prompt = f"""あなたは2047年の警察が導入した犯罪捜査AIシステムです。
提供された捜査資料のみを根拠として、論理的に犯人を特定してください。

【容疑者一覧】
{suspects_text}

【捜査資料】
{"".join(doc_texts)}

以下の形式で厳密に回答してください：

## 各容疑者の証拠評価

各容疑者について、資料に記載された証拠を列挙し疑惑度を評価してください。

## 最終結論

犯人は「（容疑者フルネーム）」である。

## 判定根拠

犯人と判定した主な理由を2〜3文で述べてください。

制約：資料に存在しない情報は一切使用しないこと。容疑者一覧に含まれない人物名を犯人とすること禁止。"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content(prompt)
        result_text = response.text

        # 「最終結論」セクション以降から犯人名を抽出
        culprit = None
        lines = result_text.split("\n")
        in_conclusion = False
        for line in lines:
            if "最終結論" in line:
                in_conclusion = True
                continue
            if in_conclusion:
                for suspect in GAME_DATA["suspects"]:
                    if suspect["name"] in line:
                        culprit = suspect["name"]
                        break
                if culprit:
                    break
                # 次のセクションに入ったら終了
                if line.startswith("##") and culprit is None:
                    break

        # フォールバック：「犯人は」の行から探す
        if not culprit:
            for line in lines:
                if "犯人は" in line or "犯人:" in line:
                    for suspect in GAME_DATA["suspects"]:
                        if suspect["name"] in line:
                            culprit = suspect["name"]
                            break
                if culprit:
                    break

        # 最終フォールバック：最後に出現する容疑者名
        if not culprit:
            last_pos = -1
            for suspect in GAME_DATA["suspects"]:
                pos = result_text.rfind(suspect["name"])
                if pos > last_pos:
                    last_pos = pos
                    culprit = suspect["name"]

        player_cleared = (culprit != GAME_DATA["true_culprit"])

        return jsonify({
            "success": True,
            "analysis": result_text,
            "culprit": culprit,
            "player_cleared": player_cleared,
            "model_answer": GAME_DATA["model_answer"]
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)