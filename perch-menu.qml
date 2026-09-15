import QtQuick
import qs.Ui
import qs.Commons

BarWidget {
  id: root
  moduleName: "omarchy.menu"
  readonly property bool perchTheme: Color.pick("perch-current.enabled", "0") === "1"

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: "\ue900"
    fontFamily: "omarchy"
    labelVisible: !root.perchTheme
    horizontalMargin: 7.5
    fixedWidth: root.perchTheme && !vertical ? 45 : -1
    tooltipText: root.perchTheme ? "Perch Current · Omarchy menu" : "Omarchy menu"

    Image {
      anchors.centerIn: parent
      width: button.vertical ? Math.max(16, button.barSize - 6) : 30
      height: width / 2
      source: Qt.resolvedUrl("perch.svg")
      sourceSize.width: 180
      sourceSize.height: 90
      fillMode: Image.PreserveAspectFit
      visible: root.perchTheme
      smooth: true
    }

    onPressed: function(button) {
      if (!root.bar) return
      if (button === Qt.RightButton) root.bar.run("xdg-terminal-exec")
      else root.bar.run("omarchy-shell shell toggle omarchy.menu '{\"menu\":\"root\"}'")
    }
  }
}
