# -*- coding: utf-8 -*-
"""
chemical-compliance.html に埋め込む物質マスタ（M_ROWS）を生成する。

内蔵マスタは「工場で実際に使われる代表物質」を対象とした出発点であり、
法令の全対象物質を網羅するものではない。安衛法のラベル・SDS・リスク
アセスメント対象物は2026年4月に約2,900物質へ拡大するため、実運用では
アプリの「物質マスタ」タブから公式リストを取り込んで補うことを前提とする。

区分コード
  an    安衛法 表示・通知対象   1=該当 0=非該当 2=要確認
  tokka 特化則  1=第1類 2T=第2類(特定第2類) 2K=第2類(管理第2類)
                2S=第2類(特別管理物質) 3=第3類
  yuki  有機則  1/2/3 = 第1種/第2種/第3種
  kakan 化管法  1=第一種 1T=特定第一種 2=第二種 ?=要確認
  doku  毒劇法  毒 / 劇
  sui   水濁法有害物質 1=該当 2=要確認
"""
import io, re, sys

S = []
def add(cas, name, **kw):
    S.append((cas, name, kw))

# ============================================================
# 有機溶剤中毒予防規則 別表（現行44物質）
# 平成26年改正で12物質が特別有機溶剤として特化則へ移行した後の構成
# ============================================================
# --- 第1種有機溶剤等（2物質） ---
add("540-59-0","1,2-ジクロロエチレン", yuki="1", shi="4|第1石油類(非水溶性)", taiki="VOC", note="二塩化アセチレン")
add("75-15-0","二硫化炭素", yuki="1", doku="劇", shi="4|特殊引火物", kakan="1", taiki="VOC", josei=1, skin=1)

# --- 第2種有機溶剤等（35物質） ---
add("67-64-1","アセトン", yuki="2", shi="4|第1石油類(水溶性)", taiki="VOC")
add("78-83-1","イソブチルアルコール", yuki="2", shi="4|第2石油類(非水溶性)", taiki="VOC", skin=1)
add("67-63-0","イソプロピルアルコール", yuki="2", shi="4|アルコール類", taiki="VOC", note="2-プロパノール／IPA")
add("123-51-3","イソペンチルアルコール", yuki="2", shi="4|第2石油類(非水溶性)", taiki="VOC", note="イソアミルアルコール")
add("60-29-7","エチルエーテル", yuki="2", shi="4|特殊引火物", taiki="VOC", note="ジエチルエーテル")
add("110-80-5","エチレングリコールモノエチルエーテル", yuki="2", kakan="1", shi="4|第2石油類(水溶性)", taiki="VOC", josei=1, skin=1, note="セロソルブ")
add("111-15-9","エチレングリコールモノエチルエーテルアセテート", yuki="2", kakan="1", shi="4|第2石油類(水溶性)", taiki="VOC", josei=1, skin=1, note="セロソルブアセテート")
add("111-76-2","エチレングリコールモノ-ノルマル-ブチルエーテル", yuki="2", kakan="1", shi="4|第3石油類(水溶性)", taiki="VOC", skin=1, note="ブチルセロソルブ")
add("109-86-4","エチレングリコールモノメチルエーテル", yuki="2", kakan="1", shi="4|第2石油類(水溶性)", taiki="VOC", josei=1, skin=1, note="メチルセロソルブ")
add("95-50-1","オルト-ジクロロベンゼン", yuki="2", kakan="1", shi="4|第3石油類(非水溶性)", taiki="VOC", skin=1)
add("1330-20-7","キシレン", yuki="2", kakan="1", shi="4|第2石油類(非水溶性)", taiki="VOC/有害大気", josei=1, skin=1)
add("1319-77-3","クレゾール", yuki="2", kakan="1", doku="劇", shi="4|第3石油類(非水溶性)", skin=1)
add("108-90-7","クロロベンゼン", yuki="2", kakan="1", shi="4|第2石油類(非水溶性)", taiki="VOC", skin=1)
add("110-19-0","酢酸イソブチル", yuki="2", shi="4|第1石油類(非水溶性)", taiki="VOC")
add("108-21-4","酢酸イソプロピル", yuki="2", shi="4|第1石油類(非水溶性)", taiki="VOC")
add("123-92-2","酢酸イソペンチル", yuki="2", shi="4|第2石油類(非水溶性)", taiki="VOC", note="酢酸イソアミル")
add("141-78-6","酢酸エチル", yuki="2", shi="4|第1石油類(非水溶性)", taiki="VOC")
add("123-86-4","酢酸ノルマル-ブチル", yuki="2", shi="4|第1石油類(非水溶性)", taiki="VOC")
add("109-60-4","酢酸ノルマル-プロピル", yuki="2", shi="4|第1石油類(非水溶性)", taiki="VOC")
add("628-63-7","酢酸ノルマル-ペンチル", yuki="2", shi="4|第2石油類(非水溶性)", taiki="VOC", note="酢酸ノルマル-アミル")
add("79-20-9","酢酸メチル", yuki="2", shi="4|第1石油類(水溶性)", taiki="VOC")
add("108-93-0","シクロヘキサノール", yuki="2", shi="4|第3石油類(非水溶性)", taiki="VOC", skin=1)
add("108-94-1","シクロヘキサノン", yuki="2", shi="4|第2石油類(非水溶性)", taiki="VOC", skin=1)
add("68-12-2","N,N-ジメチルホルムアミド", yuki="2", kakan="1", shi="4|第2石油類(水溶性)", taiki="VOC", josei=1, skin=1)
add("109-99-9","テトラヒドロフラン", yuki="2", shi="4|第1石油類(水溶性)", taiki="VOC", skin=1)
add("71-55-6","1,1,1-トリクロロエタン", yuki="2", kakan="1", taiki="有害大気", sui=1, dojo=1, note="オゾン層保護法の特定物質")
add("108-88-3","トルエン", yuki="2", kakan="1", doku="劇", shi="4|第1石油類(非水溶性)", taiki="VOC/有害大気", josei=1, skin=1)
add("110-54-3","ノルマルヘキサン", yuki="2", kakan="1", shi="4|第1石油類(非水溶性)", taiki="VOC", josei=1, skin=1, note="末梢神経障害")
add("71-36-3","1-ブタノール", yuki="2", shi="4|第2石油類(非水溶性)", taiki="VOC", skin=1, note="炭素数4のためアルコール類に該当しない")
add("78-92-2","2-ブタノール", yuki="2", shi="4|第2石油類(非水溶性)", taiki="VOC", skin=1)
add("67-56-1","メタノール", yuki="2", doku="劇", shi="4|アルコール類", taiki="VOC", josei=1, skin=1)
add("78-93-3","メチルエチルケトン", yuki="2", shi="4|第1石油類(非水溶性)", taiki="VOC", skin=1, note="消防法上は非水溶性区分")
add("25639-42-3","メチルシクロヘキサノール", yuki="2", shi="4|第3石油類(非水溶性)", taiki="VOC", skin=1)
add("1331-22-2","メチルシクロヘキサノン", yuki="2", shi="4|第2石油類(非水溶性)", taiki="VOC", skin=1)
add("591-78-6","メチル-ノルマル-ブチルケトン", yuki="2", shi="4|第2石油類(非水溶性)", taiki="VOC", skin=1, note="2-ヘキサノン")

# --- 第3種有機溶剤等（7物質・石油系） ---
add("-","ガソリン", yuki="3", shi="4|第1石油類(非水溶性)", taiki="VOC", note="ベンゼン含有により特化則の適用を要確認")
add("-","コールタールナフサ", yuki="3", shi="4|第1石油類(非水溶性)", taiki="VOC")
add("8032-32-4","石油エーテル", yuki="3", shi="4|特殊引火物", taiki="VOC")
add("-","石油ナフサ", yuki="3", shi="4|第1石油類(非水溶性)", taiki="VOC")
add("-","石油ベンジン", yuki="3", shi="4|第1石油類(非水溶性)", taiki="VOC")
add("8006-64-2","テレビン油", yuki="3", shi="4|第2石油類(非水溶性)", taiki="VOC")
add("8052-41-3","ミネラルスピリット", yuki="3", shi="4|第2石油類(非水溶性)", taiki="VOC", note="ホワイトスピリット／ミネラルシンナー")

# ============================================================
# 特定化学物質障害予防規則
#   tokka は 1/2/3（第1類・第2類・第3類）。特定第2類と管理第2類の細分は
#   設備要件にのみ関わり、作業主任者・測定・健診・定期自主検査の要否は
#   変わらないため、確度を優先して細分は持たせず備考で補う。
#   sp=1 は特別管理物質（作業記録および各記録の30年保存の対象）。
# ============================================================
# --- 第1類物質（製造許可物質・7物質） ---
add("91-94-1","ジクロロベンジジン及びその塩", tokka="1", sp=1, cancer=1, kakan="1T", doku="劇", josei=1, note="製造許可が必要")
add("134-32-7","アルファ-ナフチルアミン及びその塩", tokka="1", sp=1, cancer=1, doku="劇", note="製造許可が必要")
add("1336-36-3","塩素化ビフェニル", tokka="1", cancer=1, kakan="1T", sui=1, josei=1, note="PCB。PCB特別措置法の対象。製造許可が必要")
add("119-93-7","オルト-トリジン及びその塩", tokka="1", sp=1, cancer=1, doku="劇", note="製造許可が必要")
add("119-90-4","ジアニシジン及びその塩", tokka="1", sp=1, cancer=1, kakan="1T", doku="劇", note="製造許可が必要")
add("7440-41-7","ベリリウム及びその化合物", tokka="1", sp=1, cancer=1, kakan="1T", doku="毒", josei=1, note="製造許可が必要")
add("98-07-7","ベンゾトリクロリド", tokka="1", sp=1, cancer=1, kakan="1T", doku="劇", note="製造許可が必要")

# --- 特別有機溶剤等（12物質・平成26年に有機則から移行） ---
add("100-41-4","エチルベンゼン", tokka="2", sp=1, cancer=1, kakan="1", shi="4|第1石油類(非水溶性)", taiki="VOC/有害大気", josei=1, skin=1, note="塗装業務で特化則を適用。特別有機溶剤")
add("67-66-3","クロロホルム", tokka="2", sp=1, cancer=1, kakan="1", doku="劇", taiki="有害大気", sui=1, dojo=1, josei=1, skin=1, note="特別有機溶剤")
add("56-23-5","四塩化炭素", tokka="2", sp=1, cancer=1, kakan="1", doku="劇", taiki="有害大気", sui=1, dojo=1, josei=1, skin=1, note="特別有機溶剤。オゾン層保護法の特定物質")
add("123-91-1","1,4-ジオキサン", tokka="2", sp=1, cancer=1, kakan="1", shi="4|第1石油類(水溶性)", taiki="有害大気", sui=1, josei=1, skin=1, note="特別有機溶剤。有機則第2種から移行")
add("107-06-2","1,2-ジクロロエタン", tokka="2", sp=1, cancer=1, kakan="1T", doku="劇", shi="4|第1石油類(非水溶性)", taiki="有害大気", sui=1, dojo=1, josei=1, skin=1, note="特別有機溶剤")
add("78-87-5","1,2-ジクロロプロパン", tokka="2", sp=1, cancer=1, kakan="1", shi="4|第1石油類(非水溶性)", josei=1, skin=1, note="胆管がん事案を受け特化則へ追加。特別有機溶剤")
add("75-09-2","ジクロロメタン", tokka="2", sp=1, cancer=1, kakan="1", taiki="有害大気", josei=1, skin=1, note="特別有機溶剤。有機則第2種から移行")
add("100-42-5","スチレン", tokka="2", cancer=0, kakan="1", shi="4|第2石油類(非水溶性)", taiki="VOC/有害大気", josei=1, skin=1, note="特別有機溶剤。特別管理物質ではない")
add("79-34-5","1,1,2,2-テトラクロロエタン", tokka="2", sp=1, cancer=1, kakan="1", doku="劇", taiki="有害大気", sui=1, josei=1, skin=1, note="特別有機溶剤")
add("127-18-4","テトラクロロエチレン", tokka="2", sp=1, cancer=1, kakan="1T", doku="劇", taiki="有害大気", sui=1, dojo=1, josei=1, skin=1, note="特別有機溶剤")
add("79-01-6","トリクロロエチレン", tokka="2", sp=1, cancer=1, kakan="1T", doku="劇", taiki="有害大気", sui=1, dojo=1, josei=1, skin=1, note="特別有機溶剤。地下水汚染の代表物質")
add("108-10-1","メチルイソブチルケトン", tokka="2", kakan="1", shi="4|第1石油類(非水溶性)", taiki="VOC", skin=1, note="特別有機溶剤。有機則第2種から移行。特別管理物質ではない")

# --- 第2類物質（その他） ---
add("79-06-1","アクリルアミド", tokka="2", sp=1, cancer=1, kakan="1", doku="劇", josei=1, skin=1)
add("107-13-1","アクリロニトリル", tokka="2", sp=1, cancer=1, kakan="1T", doku="劇", shi="4|第1石油類(非水溶性)", taiki="有害大気", josei=1, skin=1)
add("151-56-4","エチレンイミン", tokka="2", sp=1, cancer=1, kakan="1", doku="劇", josei=1, skin=1)
add("75-21-8","エチレンオキシド", tokka="2", sp=1, cancer=1, kakan="1T", doku="劇", taiki="有害大気", josei=1, note="酸化エチレン。滅菌用途")
add("75-01-4","塩化ビニル", tokka="2", sp=1, cancer=1, kakan="1T", taiki="有害大気", josei=1, note="高圧ガス保安法も要確認")
add("7782-50-5","塩素", tokka="2", kakan="1", doku="劇", taiki="特定物質", note="高圧ガス保安法も要確認")
add("492-80-8","オーラミン", tokka="2", sp=1, cancer=1, josei=1)
add("91-15-6","オルト-フタロジニトリル", tokka="2", kakan="1", doku="劇")
add("7440-43-9","カドミウム及びその化合物", tokka="2", cancer=1, kakan="1T", doku="毒", sui=1, dojo=1, josei=1)
add("7775-11-3","クロム酸ナトリウム", tokka="2", sp=1, cancer=1, kakan="1T", doku="劇", shi="1|酸化性固体 第2種", sui=1, dojo=1, josei=1, note="六価クロム化合物")
add("7789-00-6","クロム酸カリウム", tokka="2", sp=1, cancer=1, kakan="1T", doku="劇", shi="1|酸化性固体 第2種", sui=1, dojo=1, josei=1, note="六価クロム化合物")
add("7778-50-9","重クロム酸カリウム", tokka="2", sp=1, cancer=1, kakan="1T", doku="劇", shi="1|酸化性固体 第2種", sui=1, dojo=1, josei=1, note="六価クロム化合物")
add("10588-01-9","重クロム酸ナトリウム", tokka="2", sp=1, cancer=1, kakan="1T", doku="劇", shi="1|酸化性固体 第2種", sui=1, dojo=1, josei=1, note="六価クロム化合物")
add("1333-82-0","三酸化クロム", tokka="2", sp=1, cancer=1, kakan="1T", doku="劇", shi="1|酸化性固体 第1種", sui=1, dojo=1, josei=1, note="無水クロム酸。硬質クロムめっき")
add("107-30-2","クロロメチルメチルエーテル", tokka="2", sp=1, cancer=1, doku="劇", shi="4|第1石油類(非水溶性)")
add("1314-62-1","五酸化バナジウム", tokka="2", cancer=1, kakan="1", doku="劇", josei=1)
add("8007-45-2","コールタール", tokka="2", sp=1, cancer=1, kakan="1")
add("75-56-9","酸化プロピレン", tokka="2", sp=1, cancer=1, kakan="1T", shi="4|特殊引火物", taiki="有害大気")
add("151-50-8","シアン化カリウム", tokka="2", kakan="1", doku="毒", taiki="特定物質", sui=1, skin=1, note="毒劇法の業務上取扱者届出の対象となる場合あり")
add("74-90-8","シアン化水素", tokka="2", kakan="1", doku="毒", shi="4|第1石油類(水溶性)", taiki="特定物質", sui=1, skin=1)
add("143-33-9","シアン化ナトリウム", tokka="2", kakan="1", doku="毒", taiki="特定物質", sui=1, skin=1, note="毒劇法の業務上取扱者届出の対象となる場合あり")
add("101-14-4","3,3'-ジクロロ-4,4'-ジアミノジフェニルメタン", tokka="2", sp=1, cancer=1, kakan="1T", doku="劇", josei=1, skin=1, note="MOCA。ウレタン硬化剤")
add("74-83-9","臭化メチル", tokka="2", kakan="1", doku="劇", taiki="有害大気", note="オゾン層保護法の特定物質")
add("7439-97-6","水銀及びその無機化合物", tokka="2", kakan="1", doku="毒", taiki="水銀等", sui=1, dojo=1, josei=1, note="水銀に関する水俣条約の対応も要確認")
add("584-84-9","トリレンジイソシアネート", tokka="2", kakan="1", doku="劇", skin=1, note="TDI。ウレタン原料")
add("91-20-3","ナフタレン", tokka="2", sp=1, cancer=1, kakan="1", taiki="有害大気", skin=1)
add("13463-39-3","ニッケルカルボニル", tokka="2", sp=1, cancer=1, kakan="1T", doku="毒", shi="4|第1石油類(非水溶性)")
add("7786-81-4","硫酸ニッケル", tokka="2", sp=1, cancer=1, kakan="1", doku="劇", sui=2, josei=1, skin=1, note="ニッケル化合物。めっき薬品")
add("7718-54-9","塩化ニッケル(II)", tokka="2", sp=1, cancer=1, kakan="1", doku="劇", sui=2, josei=1, skin=1, note="ニッケル化合物。めっき薬品")
add("628-96-6","ニトログリコール", tokka="2", doku="劇", shi="5|自己反応性 第1種", skin=1)
add("60-11-7","パラ-ジメチルアミノアゾベンゼン", tokka="2", sp=1, cancer=1, josei=1)
add("100-00-5","パラ-ニトロクロロベンゼン", tokka="2", kakan="1", doku="毒", skin=1)
add("7664-39-3","ふっ化水素", tokka="2", kakan="1", doku="毒", taiki="特定物質", sui=1, skin=1, note="ふっ素として排水規制")
add("57-57-8","ベータ-プロピオラクトン", tokka="2", sp=1, cancer=1, skin=1)
add("71-43-2","ベンゼン", tokka="2", sp=1, cancer=1, kakan="1T", doku="劇", shi="4|第1石油類(非水溶性)", taiki="有害大気", sui=1, dojo=1, josei=1, skin=1, note="含有1%超で特化則を適用")
add("87-86-5","ペンタクロロフェノール", tokka="2", kakan="1", doku="劇", sui=1, josei=1)
add("632-99-5","マゼンタ", tokka="2", sp=1, cancer=1)
add("7439-96-5","マンガン及びその化合物", tokka="2", kakan="1", josei=1)
add("74-88-4","沃化メチル", tokka="2", kakan="1", doku="劇", shi="4|第1石油類(非水溶性)")
add("142844-00-6","リフラクトリーセラミックファイバー", tokka="2", sp=1, cancer=1, note="RCF。耐火断熱材")
add("7783-06-4","硫化水素", tokka="2", kakan="1", doku="劇", taiki="特定物質", note="酸素欠乏症等防止規則も要確認")
add("77-78-1","硫酸ジメチル", tokka="2", sp=1, cancer=1, kakan="1", doku="毒", josei=1, skin=1)
add("50-00-0","ホルムアルデヒド", tokka="2", sp=1, cancer=1, kakan="1T", doku="劇", taiki="有害大気", josei=1, skin=1, note="ホルマリン水溶液も対象")
add("302-01-2","ヒドラジン", tokka="2", sp=1, cancer=1, kakan="1", doku="劇", josei=1, skin=1, note="ボイラ脱酸素剤")
add("57-14-7","1,1-ジメチルヒドラジン", tokka="2", sp=1, cancer=1, doku="劇", shi="4|第1石油類(水溶性)")
add("7440-48-4","コバルト及びその無機化合物", tokka="2", sp=1, cancer=1, kakan="1", josei=1, skin=1)
add("1309-64-4","三酸化二アンチモン", tokka="2", sp=1, cancer=1, kakan="1", josei=1, note="難燃助剤")
add("7440-38-2","砒素及びその化合物", tokka="2", sp=1, cancer=1, kakan="1T", doku="毒", sui=1, dojo=1, josei=1)
add("-","インジウム化合物", tokka="2", sp=1, cancer=1, note="ITOターゲット等")
add("62-73-7","ジメチル-2,2-ジクロロビニルホスフェイト", tokka="2", sp=1, cancer=1, kakan="1", doku="劇", note="DDVP")
add("-","溶接ヒューム", tokka="2", cancer=1, note="金属アーク溶接等作業。令和3年4月から特化則。じん肺法も対象。特別管理物質ではない")

# --- 第3類物質（8物質・大量漏えい防止が主眼） ---
add("7664-41-7","アンモニア", tokka="3", kakan="1", doku="劇", taiki="特定物質", note="高圧ガス保安法・悪臭防止法も要確認")
add("630-08-0","一酸化炭素", tokka="3", josei=1)
add("7647-01-0","塩化水素", tokka="3", kakan="1", doku="劇", taiki="特定物質", note="塩酸")
add("7697-37-2","硝酸", tokka="3", doku="劇", shi="6|酸化性液体", taiki="特定物質")
add("7446-09-5","二酸化硫黄", tokka="3", taiki="特定物質", note="ばい煙の硫黄酸化物も要確認")
add("108-95-2","フェノール", tokka="3", kakan="1", doku="劇", shi="4|第3石油類(非水溶性)", skin=1)
add("75-44-5","ホスゲン", tokka="3", kakan="1", doku="毒", taiki="特定物質")
add("7664-93-9","硫酸", tokka="3", doku="劇", note="水濁法は水素イオン濃度で規制")

# ============================================================
# 鉛則・四アルキル鉛則・粉じん則・じん肺法・石綿則
# ============================================================
add("7439-92-1","鉛及びその化合物", lead=1, cancer=1, kakan="1", doku="劇", sui=1, dojo=1, josei=1, note="鉛業務に該当するかの確認が必要")
add("1317-36-8","一酸化鉛", lead=1, cancer=1, kakan="1", doku="劇", sui=1, dojo=1, josei=1, note="リサージ")
add("1314-41-6","鉛丹", lead=1, cancer=1, kakan="1", doku="劇", sui=1, dojo=1, josei=1, note="四酸化三鉛。さび止め塗料")
add("7446-14-2","硫酸鉛", lead=1, cancer=1, kakan="1", doku="劇", sui=1, dojo=1, josei=1)
add("7758-97-6","クロム酸鉛", lead=1, sp=1, cancer=1, kakan="1T", doku="劇", sui=1, dojo=1, josei=1, note="鉛クロメート顔料。六価クロム化合物でもある")
add("78-00-2","四エチル鉛", lead=1, cancer=1, doku="毒", sui=1, josei=1, note="四アルキル鉛中毒予防規則の対象")
add("14808-60-7","結晶質シリカ(石英)", dust=1, cancer=1, note="じん肺法の対象。研削・鋳造・耐火物")
add("14464-46-1","クリストバライト", dust=1, cancer=1, note="じん肺法の対象")
add("14807-96-6","滑石(タルク)", dust=1, note="じん肺法の対象")
add("13463-67-7","酸化チタン(IV)", dust=1, note="粉状のものは粉じん則の対象")
add("1333-86-4","カーボンブラック", dust=1, cancer=1)
add("409-21-2","炭化ケイ素", dust=1)
add("1332-21-4","石綿", cancer=1, kashin="1特", taiki="特定粉じん", josei=1, note="製造等禁止。石綿則および大気汚染防止法の事前調査対象")
add("12001-29-5","クリソタイル", cancer=1, kashin="1特", taiki="特定粉じん", josei=1, note="白石綿。製造等禁止")
add("12172-73-5","アモサイト", cancer=1, kashin="1特", taiki="特定粉じん", josei=1, note="茶石綿。製造等禁止")
add("12001-28-4","クロシドライト", cancer=1, kashin="1特", taiki="特定粉じん", josei=1, note="青石綿。製造等禁止")

# ============================================================
# 工場で常用する酸・アルカリ・酸化剤・めっき薬品（毒劇法・消防法・化管法）
# ============================================================
add("1310-73-2","水酸化ナトリウム", doku="劇", note="水濁法は水素イオン濃度で規制")
add("1310-58-3","水酸化カリウム", doku="劇")
add("7722-84-1","過酸化水素", doku="劇", shi="6|酸化性液体", note="6%以下は劇物から除外。消防法は36%以上")
add("7722-64-7","過マンガン酸カリウム", doku="劇", shi="1|酸化性固体 第2種", note="覚醒剤原料の規制対象")
add("64-19-7","酢酸", doku="劇", shi="4|第2石油類(水溶性)", note="90%以下は劇物から除外")
add("108-24-7","無水酢酸", doku="劇", shi="4|第2石油類(水溶性)", note="麻薬及び向精神薬取締法の原料。届出・記録が必要な場合がある")
add("7664-38-2","りん酸", doku="劇")
add("7681-52-9","次亜塩素酸ナトリウム", doku="劇", note="酸と混触で塩素ガスが発生")
add("7632-00-0","亜硝酸ナトリウム", doku="劇", shi="1|酸化性固体 第2種")
add("7631-99-4","硝酸ナトリウム", shi="1|酸化性固体 第3種")
add("7757-79-1","硝酸カリウム", shi="1|酸化性固体 第3種")
add("6484-52-2","硝酸アンモニウム", shi="1|酸化性固体 第3種")
add("7775-09-9","塩素酸ナトリウム", doku="劇", shi="1|酸化性固体 第1種")
add("7601-90-3","過塩素酸", doku="劇", shi="6|酸化性液体")
add("94-36-0","過酸化ベンゾイル", shi="5|自己反応性 第2種", skin=1)
add("144-62-7","しゅう酸", doku="劇")
add("7758-98-7","硫酸銅(II)", doku="劇", kakan="1", sui=2, note="銅水溶性塩")
add("7705-08-0","塩化鉄(III)", doku="劇", note="塩化第二鉄。エッチング液")
add("1341-49-7","ふっ化水素アンモニウム", doku="劇", kakan="1", sui=1, note="ふっ素として排水規制")
add("10043-35-3","ほう酸", kakan="1", sui=2, note="ほう素及びその化合物として排水規制")
add("1317-33-5","二硫化モリブデン", kakan="1", note="固体潤滑剤")
add("-","亜鉛の水溶性化合物", kakan="1", sui=2, note="排水基準の亜鉛含有量に関わる")

# ============================================================
# 樹脂・塗料・接着剤の原料（化管法・消防法）
# ============================================================
add("80-62-6","メタクリル酸メチル", kakan="1", doku="劇", shi="4|第1石油類(非水溶性)", taiki="VOC", skin=1)
add("79-10-7","アクリル酸", kakan="1", doku="劇", shi="4|第2石油類(水溶性)", skin=1)
add("140-88-5","アクリル酸エチル", kakan="1", doku="劇", shi="4|第1石油類(非水溶性)", taiki="VOC", skin=1)
add("108-05-4","酢酸ビニル", kakan="1", shi="4|第1石油類(非水溶性)", taiki="VOC")
add("106-89-8","エピクロロヒドリン", cancer=1, kakan="1", doku="劇", shi="4|第2石油類(非水溶性)", taiki="有害大気", skin=1, note="エポキシ樹脂原料。特定第一種該当性を要確認")
add("80-05-7","ビスフェノールA", kakan="1", note="エポキシ樹脂原料")
add("101-68-8","ジフェニルメタン-4,4'-ジイソシアネート", kakan="1", skin=1, note="MDI。ウレタン原料")
add("822-06-0","ヘキサメチレン-1,6-ジイソシアネート", kakan="1", doku="劇", skin=1, note="HDI。ウレタン塗料硬化剤")
add("107-21-1","エチレングリコール", kakan="1", shi="4|第3石油類(水溶性)")
add("111-46-6","ジエチレングリコール", shi="4|第3石油類(水溶性)")
add("57-55-6","プロピレングリコール", an=0, shi="4|第3石油類(水溶性)")
add("56-81-5","グリセリン", an=0, shi="4|第3石油類(水溶性)")
add("872-50-4","N-メチル-2-ピロリドン", kakan="1", shi="4|第3石油類(水溶性)", taiki="VOC", josei=1, skin=1, note="女性則の就業制限対象")
add("67-68-5","ジメチルスルホキシド", shi="4|第3石油類(水溶性)", skin=1, note="DMSO。皮膚吸収に注意")
add("107-98-2","プロピレングリコールモノメチルエーテル", shi="4|第2石油類(水溶性)", taiki="VOC", note="PGME")
add("108-65-6","プロピレングリコールモノメチルエーテルアセテート", shi="4|第2石油類(非水溶性)", taiki="VOC", note="PGMEA")
add("97-64-3","乳酸エチル", shi="4|第2石油類(水溶性)", taiki="VOC")
add("123-42-2","ジアセトンアルコール", shi="4|第2石油類(水溶性)", taiki="VOC")
add("121-44-8","トリエチルアミン", kakan="1", doku="劇", shi="4|第1石油類(水溶性)", skin=1)
add("111-42-2","ジエタノールアミン", kakan="1", skin=1)
add("110-91-8","モルホリン", kakan="1", doku="劇", shi="4|第2石油類(水溶性)", skin=1)
add("107-15-3","エチレンジアミン", kakan="1", doku="劇", shi="4|第2石油類(水溶性)", skin=1)
add("-","直鎖アルキルベンゼンスルホン酸及びその塩", kakan="1", note="洗浄剤の界面活性剤")
add("-","ポリ(オキシエチレン)アルキルエーテル", kakan="1", note="洗浄剤の界面活性剤")

# ============================================================
# 燃料・油・アルコール類（消防法中心）
# ============================================================
add("64-17-5","エタノール", shi="4|アルコール類", taiki="VOC", note="有機則の対象外")
add("71-23-8","1-プロパノール", shi="4|アルコール類", taiki="VOC", skin=1)
add("-","灯油", shi="4|第2石油類(非水溶性)", taiki="VOC")
add("-","軽油", shi="4|第2石油類(非水溶性)", taiki="VOC")
add("-","重油", shi="4|第3石油類(非水溶性)", note="燃料として燃焼させる場合は大気汚染防止法のばい煙を要確認")
add("-","潤滑油・鉱油", an=0, shi="4|第4石油類", note="廃棄時は廃油として産業廃棄物")
add("-","切削油(水溶性)", an=2, skin=2, kakan="?", note="配合成分のSDSで個別に判定が必要")
add("-","切削油(不水溶性)", an=2, shi="4|第4石油類", note="配合成分のSDSで個別に判定が必要。引火点により品名が変わる")
add("-","動植物油", shi="4|動植物油類")

# ============================================================
# 可燃性固体・禁水性物質（消防法）
# ============================================================
add("7429-90-5","アルミニウム粉", dust=1, shi="2|金属粉・マグネシウム 第2種")
add("7439-95-4","マグネシウム", shi="2|金属粉・マグネシウム 第2種")
add("7440-66-6","亜鉛粉", shi="2|金属粉・マグネシウム 第2種", sui=2)
add("7439-89-6","鉄粉", dust=1, shi="2|鉄粉")
add("7704-34-9","硫黄", shi="2|硫黄・赤りん・硫化りん")
add("7723-14-0","赤りん", shi="2|硫黄・赤りん・硫化りん")
add("12185-10-3","黄りん", doku="毒", shi="3|黄りん", kakan="1")
add("7440-23-5","ナトリウム", shi="3|自然発火性・禁水性 第1種")
add("1305-78-8","酸化カルシウム", doku="劇", note="生石灰。水と反応して発熱")

# ============================================================
# 高圧ガス（高圧ガス保安法）
# ============================================================
add("7727-37-9","窒素", an=0, note="高圧ガス保安法。単純窒息性ガス。酸素欠乏に注意")
add("7440-37-1","アルゴン", an=0, note="高圧ガス保安法。単純窒息性ガス")
add("7782-44-7","酸素", note="高圧ガス保安法。支燃性ガス")
add("124-38-9","二酸化炭素", an=0, note="高圧ガス保安法。単純窒息性ガス")
add("74-86-2","アセチレン", note="高圧ガス保安法。可燃性ガス")
add("1333-74-0","水素", note="高圧ガス保安法。可燃性ガス")
add("7440-59-7","ヘリウム", an=0, note="高圧ガス保安法。単純窒息性ガス")
add("74-98-6","プロパン", note="高圧ガス保安法。液化石油ガス")
add("106-97-8","ブタン", note="高圧ガス保安法。液化石油ガス")

# ============================================================
# 生成
# ============================================================
KEYS = ["cas","name","an","skin","cancer","tokka","sp","yuki","lead","dust",
        "kakan","doku","shi","kashin","taiki","sui","dojo","josei","note"]
DEF  = {"an":1,"skin":0,"cancer":0,"tokka":"","sp":0,"yuki":"","lead":0,"dust":0,
        "kakan":"","doku":"","shi":"","kashin":"","taiki":"","sui":0,"dojo":0,"josei":0,"note":""}

merged, order, dups = {}, [], []
for cas, name, kw in S:
    key = cas if cas and cas != "-" else "name:" + name
    if key in merged:
        dups.append((key, merged[key]["name"], name))
        merged[key].update({k: v for k, v in kw.items() if v not in ("", 0)})
        continue
    row = dict(DEF); row.update(kw); row["cas"] = cas; row["name"] = name
    merged[key] = row; order.append(key)

rows = [merged[k] for k in order]

def js(v):
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return str(int(v))

out = ["const M_KEYS=[" + ",".join('"%s"' % k for k in KEYS) + "];", "const M_ROWS=["]
out += ["[" + ",".join(js(r[k]) for k in KEYS) + "]," for r in rows]
out[-1] = out[-1].rstrip(",")
out.append("];")
block = "\n".join(out)

path = "chemical-compliance.html"
html = io.open(path, encoding="utf-8").read()
start = html.index("const M_KEYS=[")
end   = html.index("];", html.index("const M_ROWS=[")) + 2
html  = html[:start] + block + html[end:]
html  = re.sub(r'const MASTER_REV = "[^"]*";',
               'const MASTER_REV = "%d物質・代表物質シード";' % len(rows), html)
io.open(path, "w", encoding="utf-8").write(html)

print("収録物質数: %d" % len(rows))
for law, f in [("特化則 第1類", lambda r: r["tokka"]=="1"),
               ("特化則 第2類", lambda r: r["tokka"]=="2"),
               ("特化則 第3類", lambda r: r["tokka"]=="3"),
               ("うち特別管理物質", lambda r: r["sp"]==1),
               ("有機則 第1種", lambda r: r["yuki"]=="1"),
               ("有機則 第2種", lambda r: r["yuki"]=="2"),
               ("有機則 第3種", lambda r: r["yuki"]=="3"),
               ("鉛則", lambda r: r["lead"]==1),
               ("粉じん則", lambda r: r["dust"]==1),
               ("化管法", lambda r: r["kakan"] in ("1","1T","2")),
               ("毒物", lambda r: r["doku"]=="毒"),
               ("劇物", lambda r: r["doku"]=="劇"),
               ("消防法 危険物", lambda r: bool(r["shi"])),
               ("水濁法 有害物質", lambda r: r["sui"]==1),
               ("がん原性物質", lambda r: r["cancer"]==1),
               ("皮膚等障害", lambda r: r["skin"]==1)]:
    print("  %-16s %3d" % (law, sum(1 for r in rows if f(r))))

# ------------------------------------------------------------
# 参照用CSV（アプリの「マスタをCSVで書き出し」と同じ列構成）
# 社内サーバでこのHTMLと同じ場所に chem-master.csv として置くと
# 起動時に自動で読み込まれる。
# ------------------------------------------------------------
SHOBO_LABEL = {
 "4|特殊引火物":"第4類 特殊引火物","4|第1石油類(非水溶性)":"第4類 第1石油類 非水溶性",
 "4|第1石油類(水溶性)":"第4類 第1石油類 水溶性","4|アルコール類":"第4類 アルコール類",
 "4|第2石油類(非水溶性)":"第4類 第2石油類 非水溶性","4|第2石油類(水溶性)":"第4類 第2石油類 水溶性",
 "4|第3石油類(非水溶性)":"第4類 第3石油類 非水溶性","4|第3石油類(水溶性)":"第4類 第3石油類 水溶性",
 "4|第4石油類":"第4類 第4石油類","4|動植物油類":"第4類 動植物油類",
 "1|酸化性固体 第1種":"第1類 酸化性固体 第1種","1|酸化性固体 第2種":"第1類 酸化性固体 第2種",
 "1|酸化性固体 第3種":"第1類 酸化性固体 第3種","2|硫黄・赤りん・硫化りん":"第2類 硫黄・赤りん・硫化りん",
 "2|金属粉・マグネシウム 第1種":"第2類 金属粉・マグネシウム 第1種","2|鉄粉":"第2類 鉄粉",
 "2|金属粉・マグネシウム 第2種":"第2類 金属粉・マグネシウム 第2種","2|引火性固体":"第2類 引火性固体",
 "3|黄りん":"第3類 黄りん","3|自然発火性・禁水性 第1種":"第3類 自然発火性物質・禁水性物質 第1種",
 "3|自然発火性・禁水性 第2種":"第3類 自然発火性物質・禁水性物質 第2種",
 "3|自然発火性・禁水性 第3種":"第3類 自然発火性物質・禁水性物質 第3種",
 "5|自己反応性 第1種":"第5類 自己反応性物質 第1種","5|自己反応性 第2種":"第5類 自己反応性物質 第2種",
 "6|酸化性液体":"第6類 酸化性液体"}
KAKAN_LABEL = {"1":"第一種","1T":"特定第一種","2":"第二種","?":"要確認"}
CSV_COLS = [
 ("CAS番号",       lambda r: r["cas"]),
 ("物質名",        lambda r: r["name"]),
 ("安衛法",        lambda r: "対象物" if r["an"]==1 else ("要確認" if r["an"]==2 else "非該当")),
 ("皮膚等障害",    lambda r: "該当" if r["skin"]==1 else ("要確認" if r["skin"]==2 else "")),
 ("がん原性",      lambda r: "該当" if r["cancer"]==1 else ""),
 ("特化則",        lambda r: ("第%s類" % r["tokka"]) if r["tokka"] else ""),
 ("特別管理物質",  lambda r: "該当" if r["sp"]==1 else ""),
 ("有機則",        lambda r: ("第%s種" % r["yuki"]) if r["yuki"] else ""),
 ("鉛則",          lambda r: "該当" if r["lead"]==1 else ""),
 ("粉じん則",      lambda r: "該当" if r["dust"]==1 else ""),
 ("化管法",        lambda r: KAKAN_LABEL.get(r["kakan"], "")),
 ("毒劇法",        lambda r: (r["doku"]+"物") if r["doku"] else ""),
 ("消防法品名",    lambda r: SHOBO_LABEL.get(r["shi"], "")),
 ("化審法",        lambda r: "第一種特定" if r["kashin"]=="1特" else ""),
 ("大防法",        lambda r: r["taiki"]),
 ("水濁法有害物質",lambda r: "該当" if r["sui"]==1 else ("要確認" if r["sui"]==2 else "")),
 ("土対法",        lambda r: "該当" if r["dojo"]==1 else ""),
 ("女性則",        lambda r: "該当" if r["josei"]==1 else ""),
 ("備考",          lambda r: r["note"]),
 ("出所",          lambda r: "内蔵"),
]
def cell(v): return '"' + str(v).replace('"', '""') + '"'
csv_lines = [",".join(cell(c[0]) for c in CSV_COLS)]
csv_lines += [",".join(cell(c[1](r)) for c in CSV_COLS) for r in rows]
io.open("chem-master.csv", "w", encoding="utf-8-sig").write("\r\n".join(csv_lines) + "\r\n")
print("\nchem-master.csv を出力しました（%d行）" % len(rows))

for shi in set(r["shi"] for r in rows if r["shi"]):
    if shi not in SHOBO_LABEL:
        print("  !! 消防法品名の対応表に無いキー:", shi)

if dups:
    print("\n統合した重複 %d件:" % len(dups))
    for k, a, b in dups: print("  %s : %s / %s" % (k, a, b))
