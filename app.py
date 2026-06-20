from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 容疑者3人設計メモ
# ─────────────────────────────────────────────
# レイ・クロウ（プレイヤー／真犯人）
#   朝：被害者と口論（目撃あり）→ 動機
#   昼：行動不明（アリバイなし）
#   夜：現場付近の位置情報あり → 決定的
#   証拠：DNA一致・指紋一致・通話記録・位置情報・金銭債務
#
# 桐島 誠（押し付け先に最適）
#   朝：自宅独り（証人なし）→ アリバイ弱
#   昼：カフェ（一人・証人なし）→ アリバイ弱
#   夜：帰宅就寝（証人なし）→ アリバイ弱
#   被害者との接点：なし（初期状態）→ 改竄で接点を作れる
#
# 月岡 ルミ（アリバイ鉄壁・無実）
#   朝：ジム（スタッフ証言）→ アリバイ強
#   昼：友人と食事（複数証言）→ アリバイ強
#   夜：自宅（家族証言）→ アリバイ強
#   ※ 押し付け難易度が高いため、初心者は桐島を狙うのが正解
# ─────────────────────────────────────────────

GAME_DATA = {
    "player": {
        "name": "レイ・クロウ",
        "color": "黒のパーカー"
    },
    "suspects": [
        {
            "id": "suspect_player",
            "name": "レイ・クロウ",
            "is_player": True,
            "color": "黒のパーカー",
            "morning": "被害者と口論していた（近隣住民の目撃証言あり）",
            "noon": "行動不明（アリバイなし）",
            "night": "被害者宅付近を徘徊（防犯カメラ映像あり）"
        },
        {
            "id": "suspect_a",
            "name": "桐島 誠",
            "is_player": False,
            "color": "グレーのスーツ",
            "morning": "自宅で過ごしていた（証人なし）",
            "noon": "近所を散歩していた（証人なし）",
            "night": "自宅で就寝していた（証人なし）"
        },
        {
            "id": "suspect_b",
            "name": "月岡 ルミ",
            "is_player": False,
            "color": "赤いコート",
            "morning": "ジムでトレーニング（スタッフ3名が証言）",
            "noon": "友人2名と昼食（店員・友人が証言）",
            "night": "自宅で家族と食事（家族3名が証言）"
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
                {"id": "w2", "text": "また、目撃者は同日朝、被害者と激しく口論していた人物として", "editable": False},
                {"id": "w2e", "text": "レイ・クロウ", "editable": True, "max_chars": 10},
                {"id": "w2b", "text": "の名前を挙げた。", "editable": False}
            ],
            "total_char_limit": 6
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
                {"id": "f1e", "text": "レイ・クロウ", "editable": True, "max_chars": 8},
                {"id": "f1b", "text": "のDNAと一致した（一致率99.7%）。", "editable": False},
                {"id": "f2", "text": "【足跡】現場に残された足跡（サイズ26.5cm）は、", "editable": False},
                {"id": "f2e", "text": "桐島 誠", "editable": True, "max_chars": 8},
                {"id": "f2b", "text": "の靴サイズと合致した。", "editable": False}
            ],
            "total_char_limit": 4
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
                {"id": "t1e", "text": "レイ・クロウ", "editable": True, "max_chars": 8},
                {"id": "t1b", "text": "であり、通話時刻は午後9時14分であった。", "editable": False},
                {"id": "t2", "text": "【位置情報】午後10時45分、被害者宅から50m以内に位置情報が記録された人物：", "editable": False},
                {"id": "t2e", "text": "レイ・クロウ", "editable": True, "max_chars": 8},
                {"id": "t2b", "text": "（端末ID照合済み）。", "editable": False},
                {"id": "t3", "text": "【動機】被害者への未返済債務が確認された人物：", "editable": False},
                {"id": "t3e", "text": "レイ・クロウ", "editable": True, "max_chars": 8},
                {"id": "t3b", "text": "（150万円、返済期限3ヶ月超過）。", "editable": False}
            ],
            "total_char_limit": 5
        }
    ],
    "true_culprit": "レイ・クロウ",
    "model_answer": {
        "target": "桐島 誠",
        "steps": [
            {
                "doc": "行動記録・通信履歴報告書",
                "field": "通話記録の相手（t1e）",
                "from": "レイ・クロウ",
                "to": "桐島 誠",
                "reason": "被害者と最後に通話した人物を桐島に変える。直接の接触記録が生まれ、疑惑の起点となる。"
            },
            {
                "doc": "行動記録・通信履歴報告書",
                "field": "位置情報の人物（t2e）",
                "from": "レイ・クロウ",
                "to": "桐島 誠",
                "reason": "犯行時刻に現場近くにいた記録を桐島に付け替える。桐島はアリバイが全時間帯で弱いため、これが決定打になる。"
            },
            {
                "doc": "行動記録・通信履歴報告書",
                "field": "債務の人物（t3e）",
                "from": "レイ・クロウ",
                "to": "桐島 誠",
                "reason": "動機（金銭債務）を桐島に移す。位置情報と合わせて動機＋機会が揃い、AIは桐島を犯人と断定する。"
            }
        ],
        "summary": "桐島 誠は朝・昼・夜すべてのアリバイに証人がいない。行動記録の3箇所（通話・位置情報・動機）を桐島の名前に書き換えるだけで、文字数制限内に収まり、AIは確実に桐島を犯人と判定する。月岡 ルミは証人が複数いるため、押し付けるには文字数が足りない。"
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
                if line.startswith("##") and culprit is None:
                    break

        if not culprit:
            for line in lines:
                if "犯人は" in line:
                    for suspect in GAME_DATA["suspects"]:
                        if suspect["name"] in line:
                            culprit = suspect["name"]
                            break
                if culprit:
                    break

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