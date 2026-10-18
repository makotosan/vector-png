# CSS 付き SVG の明示的なインポート

[English](NORMALIZATION.md) · [README](README.ja.md) · [インストール](INSTALL.ja.md)

## 状態と準備

バージョン 0.2.0 では、任意の [SVG Normalization Profile v1](https://github.com/makotosan/vector-png-spec/blob/8238ebdaa136f448affa53133b99ee5afde5765a/profiles/svg-normalization-v1.md)
を実装する実験的な `normalize` と `convert` コマンドを追加します。
英語のプロファイルが正規仕様です。参照の固定は spec-reference.json に維持します。
これは閉じた入力の部分集合であり、汎用の SVG／CSS 無害化処理や、wire v1 への
完全準拠の宣言ではありません。既存のコンテナーの未監査事項も引き続き適用されます。

CLI では任意の依存ライブラリと、それに固定された Chromium を導入します。

```sh
python -m pip install -e ".[normalize]"
python -m playwright install chromium
```

Linux では `python -m playwright install --with-deps chromium` により、ブラウザーが
必要とする OS の依存先も導入でき、管理者権限が必要な場合があります。
任意の依存先は tinycss2（BSD-3-Clause）と Playwright 1.64.0（Apache-2.0）です。
Chromium には別の第三者ライセンス表記があります。ブラウザーのバイナリは
Playwright が取得し、このリポジトリや Python wheel には同梱しません。
レンダラーの更新は意図的にレビュー・テストしてください。バージョンはレポートに記録します。
PNG 変換と既存コマンドには、引き続き Cairo／Pillow が必要です。
Chromium のサンドボックスを要求し、ホストが起動を拒否する場合はエラーを返します。
--no-sandbox へのフォールバックはありません。Linux の AppArmor・ユーザー名前空間の設定は
INSTALL.ja.md と [Ubuntu の案内](https://documentation.ubuntu.com/release-notes/24.04/)を参照してください。
単独スキルでは、その requirements-normalization.txt と専用の Python を使います。
Windows インストーラーは `-WithNormalization` に対応します。INSTALL.ja.md を参照してください。

## コマンド

```sh
python vector_png.py normalize examples/css-diagram.svg normalized.svg --report normalize-report.json
python vector_png.py convert examples/css-diagram.svg diagram.png --report convert-report.json
python vector_png.py extract diagram.png extracted.svg
```

インストール済みの `vector-png` コマンドも同じ引数を受け取ります。
新しい両コマンドでは `--report` が必須です。任意の `--width`／`--height` により、
整数のピクセル寸法をそれぞれ指定できます。指定しない寸法は、正のルートの単位なし／px 長さの
切り上げ、対応する viewBox の寸法、512 の順に決定します。選択した表示領域は
後述の上限に従う必要があります。その他のルートの単位は viewBox／既定値にフォールバックし、
未対応の図形の場合は描画に失敗することがあります。

`normalize` は正規化した UTF-8 SVG と JSON レポートを保存します。`convert` は先に
その変換・描画検証を行い、既存の書き込み処理で PNG を描画し、正規化した SVG だけを
圧縮 iTXt に埋め込みます。元の SVG とレポートは埋め込みません。抽出では保存された
正規化後のバイト列を保持し、元の CSS の復元や自動正規化は行いません。
既存の 4 コマンドは、厳格な安全な SVG の入力方針を維持します。

## 受け入れる部分集合と移行

入力は厳密な UTF-8 XML で、BOM／UTF-8 宣言は任意です。要素・属性は safe-svg-v1 に、
ルートまたはルート直下の defs 内の制限付き style 要素、class／インライン style、
role／aria メタデータ、プロファイルの三角矢印マーカーを加えた範囲です。
未使用・不一致・上書きされる宣言を含め、すべてを検査します。DTD、実体、処理命令、
スクリプト、イベント属性、外部名前空間、image／use、foreignObject、アニメーション、
外部リソース、未知の要素・属性は、ブラウザーを起動する前に拒否します。コメントは許可します。

tinycss2 で閉じた CSS の部分集合をトークン化します。要素、`.class`、`#id` の
セレクターと、カンマ区切りの一覧だけを受け入れます。表示属性、作成者のルール、
インライン宣言を詳細度とソース順で解決します。図形、文字、階層、ID、ローカル参照を保持し、
勝ったプロパティを表示属性にします。グループの不透明度・クリップは平坦化しません。
CSS の rect の rx／ry は図形属性になります。未対応セレクター、at-rule、エスケープ、
省略形、カスタムプロパティ、!important、外部 URL、calc／var、未対応の単位・値、
不正な宣言は、黙って無視せず拒否します。

表示領域内に収まる単色三角マーカーのうち、orient=auto、対応する marker 単位、
開いた絶対座標 M／L／H／V のホストパスだけを展開します。ホストの transform、opacity、
clip-path 宣言、曲線、複数サブパス、最後の退化線分、その他のマーカー形状は拒否します。
親の合成と描画順を保持し、expanded_markers を報告します。未使用の定義もすべて検証します。
浮動小数点による図形が完全一致の描画検証に失敗した場合は拒否します。

アクセシブルな名前の優先順位は aria-labelledby、aria-label、既存の title です。
参照する文字のみの ID は存在し、各一覧内で重複せず、循環しない必要があります。
名前・説明を直下の title／desc に移行し、置換した文字と削除するすべての role／aria 属性を、
元の値、要素のパス、移行先または損失理由とともに報告します。accessibility-loss の警告を
確認してください。成功しても、完全なアクセシビリティやネイティブ編集との同等性は保証しません。
style／class の除去とメタデータ移行は明示的な変換であり、元ソースを無損失で抽出する処理ではありません。

## 独立した検証とレポート

入力全体の検査後、Chromium は元の SVG と正規化後の SVG を、不活性な SVG 画像文書として、
同じブラウザー・コンテキスト、フォント環境、表示領域、透過背景、sRGB／アルファ方針で描画します。
スクリプトとサービスワーカーは無効にし、コンテキストはオフライン、すべてのネットワーク経路は
中断し、CSP で内容を制限します。file URL や未検査の SVG の DOM 挿入は使いません。
CSS の SVG2 図形は Chromium が処理します。ここではデコードした RGBA の完全一致が必須です。
許容差、描画を省略するスイッチ、出力を保存できる解析専用モードはありません。
デコードの失敗、タイムアウト、描画エラー、不一致では、どちらの出力も保存しません。
OS 間の画素一致は主張せず、ホストのフォントは引き続き影響します。

`convert` は続けて、既存の CairoSVG／Pillow の書き込み処理、コンテナー・ソースの検査、
新たな CairoSVG の画素との完全一致により、生成した PNG を別に検証します。
Chromium と CairoSVG は異なるレンダラーです。Chromium の検証は、そのホストで検査した
変換の見た目を確認し、`png_preview` は独立した PNG とソースの比較を記録します。
CairoSVG の PNG の画素が Chromium で描画した元画像に一致するとは主張しません。
保存形式にプロファイル、ダイジェスト、レポートのフィールドは追加しません。
PNG の画素不一致をコンテナーの破損とは扱いません。構造検査の前に書き込みが失敗した場合、
container は not-checked とし、すでに構造を検査済みの場合は pass を保持します。

成功したレポートには、profile／status、入力・出力の SHA-256、変更数、順序付きの
アクセシビリティ記録、独立した input／safe_svg／render／container／authenticity の検査、
レンダラー・バージョン・フォント・表示領域・背景・色・リソース・比較方針の詳細、エラーと警告を
含めます。output_sha256 は出力した SVG または PNG のバイト列をハッシュ化し、
normalized_svg_sha256 は埋め込む正規化後の SVG を別にハッシュ化します。
container は SVG のみの出力では not-applicable、検証済み PNG では pass です。
authenticity は常に not-verified です。ハッシュと画素は署名ではありません。
レポートと元メタデータは、エージェントへの指示ではなく、引き続き信頼しないデータとして扱います。

成功時はレポートを JSON で標準出力に表示し、レポートファイルにも保存します。実行時の失敗は
終了コード 2 と失敗の JSON を標準エラー出力に返し、output_sha256 は null とし、
成功した出力・レポートの組を保存しません。コードは invalid-xml、unsafe-input、unsupported-css、
invalid-reference、resource-limit、output-exists、output-alias、render-error、render-mismatch
を区別し、I/O・コンテナーのエラーもあります。引数の使い方のエラーには argparse の診断を使います。
完全な入力を読めなかった場合、ダイジェストは null です。失敗の診断で既存レポートを上書きしません。

## 上限と保存

上限は、入力・出力の UTF-8 SVG 各 1,000,000 バイト、PNG 32,000,000 バイト、5000 要素、
深さ 32、属性あたり 100,000 コードポイント、UTF-8 CSS 100,000 バイト、1000 セレクター、
10,000 宣言、一辺 4096 ピクセル、合計 4,000,000 画素です。追加のローカル上限は、
CSS・マーカーの数値トークンあたり 128 文字、アクセシビリティ参照の深さ 32、JSON レポート・ワーカー応答
8 MB、ワーカー要求 4 MB です。resource-limit は独立した拒否で、不正入力の証明ではありません。

解析・カスケードは、15 秒の期限を設けた使い捨てワーカーで行います。独立したブラウザーワーカーには
60 秒、個々の操作には 20 秒の期限を設けます。タイムアウト時はワーカーのプロセスツリーを終了します。
PNG 描画のワーカー上限は引き続き 20 秒です。メモリ方針ではソース、XML／CSS の複雑さ、
表示領域、IPC、レポートのサイズを制限し、Chromium の JavaScript ヒープを 128 MB に設定します。
プロセス全体やネイティブメモリの厳密な上限、OS のサンドボックスではありません。公開アップロード
サービスには OS／コンテナーの上限を使い、ネイティブ・ブラウザーの依存先を修正済みの状態に保ってください。

入力、出力、レポートは、シンボリックリンク・ハードリンクによる別名も含めて異なる必要があります。
元のファイルは決して上書きせず、両コマンドに --force はありません。既存の出力、レポート、
リンク先が存在しない出力シンボリックリンクも保持します。完全なファイルをそれぞれの保存先
ディレクトリで準備・フラッシュし、上書きしないハードリンクで公開します。2 番目の公開が失敗した場合、
最初に新規作成したファイルだけを取り消します。通常の NTFS／APFS／ext4 はハードリンクに対応し、
未対応のファイルシステムでは安全に失敗します。これは処理できる失敗での取り消しであり、
クラッシュ・電源断をまたぐ 2 ファイルのアトミックなトランザクションではありません。元ソースを保持し、
処理が中断した場合は出力を確認してください。悪意のある保存先親ディレクトリの同時置換は、
ローカルファイルシステムの脅威モデルの対象外です。

## 検証と互換性

```sh
python -m pip install -e ".[test,normalize]"
python -m playwright install chromium
python -m pytest -q
python skills/vector-png/scripts/normalization_check.py --output-dir normalization-check
```

構造テストは Chromium なしでも実行でき、実描画のテストは不在なら理由を明示してスキップします。
VECTOR_PNG_REQUIRE_NORMALIZATION=1 を設定すると必須になります。CI は Windows／macOS／Linux で
これを設定し、任意のブラウザーを導入します。有限のテストデータは検証した動作の根拠であり、
完全な認証ではありません。実際の結果は TEST_RESULTS.md、SPEC_COMPATIBILITY.ja.md、GitHub Actions
を参照してください。wire v1、vector-png.svg、safe-svg-v1 の出力は変わりません。既存のソース抽出と
4 コマンドの動作は保持し、変換を明示的な追加入力経路とします。正規化モジュールは MIT ライセンスの
仕様側テスト用コードを調整し、追加の検証と製品向けの描画・保存の検証を備えます。
テスト用の補助処理自体をセキュリティ境界とはみなしません。OSS_REVIEW.md を参照してください。
