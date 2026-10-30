# MODのフォルダーとファイル

> **リファレンス** · これらを手で触る必要はありません: Studio が書きます。このページは、何かがおかしく見えるときや、ファイルを直接編集するモッダーのためのものです。

## 何がどこにあるか

| 何が | どこに |
|---|---|
| Studio のMOD | `Documents\RUSE 2.0\Mods\<mod>`（ドキュメント フォルダー）。マップの変更は `Maps`、書き出したファイルは `Exports`、バックアップは `Backups` にあります。Studio の **設定 → ファイルの保存場所** でそれぞれを開けます。編集中のものは MOD メニューの **このMODのフォルダーを表示** で開けます |
| Launcher にインストールしたMOD | `%LOCALAPPDATA%\RUSE Mod Platform\library` |
| ゲームのMOD入りのコピー | 設定で選んだフォルダー（どちらのアプリでも **MOD入りコピーの保存先**）。おすすめの場所はゲームと同じドライブの `RUSE-Instances`（たとえば `D:\RUSE-Instances`）で、そこではコピーがゲームのファイルを共有します。別のドライブでは、各コピーがゲームの完全なコピーになり、遅く、大きくなります。ゲームのクリーンなバックアップ（`RUSE-Backup`）はその隣に置かれます。 |
| ゲーム本体 | 変更されることはありません |

以前の Studio は `%LOCALAPPDATA%\RUSE Mod Platform`（`mods`、`maps`、`exports`、`mod-backups`）に保存していました。Studio は最初の起動時にそれらをドキュメントへ移し、そのことを知らせます。

## MODの中身

```
my-mod/
  mod.toml                    the mod's name, id, version, author (required)
  src/studio.rndf             unit changes made in the Studio
  text/studio.baseunite.csv   names of new units
  files/replace/gen/...png    a unit's paint (from Blender) or a unit's card, under the game texture it changes
  files/cards/<unit>.png      a new unit's own card in the build menu, named after the new unit
  files/models/<unit>.glb     a new unit's own 3D model (Import model), named after the new unit
  maps/<map pack name>/       one folder per map the mod changes:
    terrain.toml                ground brushes (also water, cover and block brushes)
    scenery.toml                buildings, props and trees placed
    scenario.toml               starting points and spawns moved, units added
    cover.toml, movement.toml   cover and movement written by hand
    map.toml                    how many players; or, for a new map, the map it copies and its name
```

## マップのフォルダー名は、マップのタイトルではなくパック名

プレイヤーはマップをタイトル（**Blitz**）で知っていますが、ゲームのファイルはパック名（**SuperCrossRoads4**）を使います。マップのフォルダーにはパック名を使わなければなりません: `maps/Blitz/` ではなく `maps/SuperCrossRoads4/` です。すべてのマップの組み合わせは [[マップ名|マップ名]] にあり、Studio のマップ一覧には両方が表示されます: 先にタイトル、点の後にパック名です。

## 新しいマップ

MODは、バトルに独自のマップを加えられます: 同梱のマップのコピーか空白のスタートで、独自の名前を付け、MODの他のファイルで作り変えます。そのフォルダー名は新しいマップのパック名（英字、数字、`_`）で、その `map.toml` に、どのマップをコピーするか、メニューで何と呼ぶかを書きます:

```toml
copy_of = "SuperCrossRoads4"   # the shipped map it starts from (its pack name: Blitz)

[name]
us = "Blitz Twin"              # English, used where a language is left out
fr = "Blitz jumeau"
```

その後は `maps/BlitzTwin/terrain.toml` などのファイルがコピーを編集し、Blitz は元のままです。バトルに並ぶマップならどれでもコピーできますが、キャンペーンとチャレンジのマップはできません。ほかのMODと同じく、2人のプレイヤーが一緒に遊ぶには同じMODが必要です。新しいマップはゲームで遊べます（2026-10-03）。Studio の **マップを複製** が、このフォルダーを作ってくれます。

## よくある間違い

| 間違い | 起きること | 直し方 |
|---|---|---|
| zip の中で、フォルダーの中にさらにフォルダーがある | Launcher は1階層下まで見て、見つけます。2階層以上下だと、MODが見つからないと表示します。 | `mod.toml` があるフォルダーを zip にしてください。 |
| マップのフォルダーにマップのタイトルを付けた | ビルドが、それはマップのパック名ではないと表示します。 | パック名に変えてください。 |
| 手で編集したファイルに入力ミスがある | MODチェックがファイルと行を示します。 | 直すか、Studio で **脇に置く**。 |
| MODの中に `.exe`、`.dll`、PC 用のスクリプトがある | 拒否されます: MODはデータだけを運びます（Studio が保存した形のゲーム自身のミッションスクリプトが、唯一の例外です）。 | 取り除いてください。 |

ファイルが読めないとき、Studio がそれを上書きすることはありません: 作業が失われることはありません。**脇に置く** は、それを元のファイルの隣で `<name>.broken.toml` に名前を変えます。

---

[[フィールドマニュアル|フィールドマニュアル]] · [[English|Mod-Folders-and-Files]]
