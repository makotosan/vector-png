# vector-png-spec を参照して開発する

[English](CONTRIBUTING.md)

## 基準と正規仕様

ファイル形式の正規仕様は [vector-png-spec](https://github.com/makotosan/vector-png-spec) です。
[spec-reference.json](spec-reference.json) で開発基準を
コミット `8238ebdaa136f448affa53133b99ee5afde5765a`（wire v1、draft 0.1）に固定します。
これはソースリポジトリの参照設定であり、PNG に埋め込む新たなフィールドではありません。
参照の固定は、実装の完全準拠を主張するものではありません。

そのリビジョンの次の文書を読んでください。

- [SPEC.md](https://github.com/makotosan/vector-png-spec/blob/8238ebdaa136f448affa53133b99ee5afde5765a/SPEC.md)：英語の規範的要件。
- [SPEC.ja.md](https://github.com/makotosan/vector-png-spec/blob/8238ebdaa136f448affa53133b99ee5afde5765a/SPEC.ja.md)：全文の日本語参考訳。
- [safe-svg-v1](https://github.com/makotosan/vector-png-spec/blob/8238ebdaa136f448affa53133b99ee5afde5765a/profiles/safe-svg-v1.md)：制限付き SVG 処理プロファイル。
- [IMPLEMENTATIONS.md](https://github.com/makotosan/vector-png-spec/blob/8238ebdaa136f448affa53133b99ee5afde5765a/IMPLEMENTATIONS.md)：実装と移行の注意事項。
- [テストデータ一覧](https://github.com/makotosan/vector-png-spec/blob/8238ebdaa136f448affa53133b99ee5afde5765a/fixtures/README.md)：利用方法と制限。
- [svg-normalization-v1](https://github.com/makotosan/vector-png-spec/blob/8238ebdaa136f448affa53133b99ee5afde5765a/profiles/svg-normalization-v1.md): 任意の入力処理プロファイルです。normalize／convert で実験的に実装しています。より厳しいローカル上限と検証は [NORMALIZATION.ja.md](NORMALIZATION.ja.md) を参照してください。

## 振る舞いを変更する前に

1. 影響する仕様の節を特定し、コンテナー、SVG プロファイル・安全性、
   プレビュー検証、CLI のどの振る舞いに関する変更かを確認します。
2. 固定した仕様の関連テストデータを確認します。コンテナーとして有効でも、
   危険な SVG や異なるプレビューを含む場合があるため、この CLI が
   自動的に受け入れられるわけではありません。
3. 意図する動作と既知の相違点を
   [SPEC_COMPATIBILITY.ja.md](SPEC_COMPATIBILITY.ja.md) に記録します。
   `vector-png.svg` の意味を黙って変更したり、保存形式に必須フィールドを加えたり、
   SVG の安全性を弱めたりしないでください。形式の変更は先に仕様リポジトリへ提案します。
4. 変更する動作を検証する実装テストを追加し、必要に応じて補助スクリプトの
   両方のコピーを更新し、関連する pytest と単独スキルの往復テストを実行します。
5. 変更説明に仕様のリビジョンと節、対象のテストデータ、テスト結果、
   互換性への影響、日英の同期確認結果を記載します。

コンテナーの妥当性、安全な SVG プロファイルへの対応、描画エンジン固有の
画素比較は区別してください。CLI の CairoSVG／RGBA 完全一致はローカルな実装方針であり、
Illustrator／Inkscape やすべての形式リーダーへの要件ではありません。

## 仕様の参照基準を更新する

上流の変更をレビューし、`main` を自動追従しないでください。
spec-reference.json の 40 文字の完全なリビジョンを置き換え、
本ガイドの固定リンクとリビジョンを日英の両方で更新します。
互換性の記録、関連テスト、影響する日英文書も同じ変更内で更新してください。
保存形式・プロファイルへの影響、新たに満たした要件と未解決の要件を明示します。
固定した参照元が取得できない場合は制限として報告し、規則を推測で作らないでください。

CI は参照設定を読み、そのリビジョンをチェックアウトしてテストデータを検査します。
これは仕様の有限のテストデータの検査であり、この CLI にすべてのデータを
入力する検証や、完全準拠の認証ではありません。実装テストと画素比較は別の検査です。

## ドキュメントと貢献

[AGENTS.md](AGENTS.md) に従ってください。存在する日英の組は全文を翻訳し、
節の順序、要件の強さ、条件、例外、数値、識別子、表、例、コマンド、参照先、
注意点、上限、状態、互換性の主張を揃えます。同じ変更内で両言語を更新し、
意味を手作業で比較してください。見出し・コード・リンクの検査だけでは同期を証明できません。
日本語の公開文書には英語の対応文書と案内リンクを用意します。
英語だけの全ドキュメントを翻訳する必要はありません。
貢献にはこのリポジトリの MIT ライセンスを適用し、依存先のライセンスは維持します。
