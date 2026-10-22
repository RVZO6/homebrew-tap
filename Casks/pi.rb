cask "pi" do
  arch arm: "arm64", intel: "x64"

  version "1.4.0"
  sha256 arm: "79d9979d76a2a5adb7c28e27e9b44629928ccd0dc9fbb6ae7217860bd5e8be5d",
         intel: "1bdefc9e1074c1de458ea9f2e43e6013ce49cd05326009b3de144037036585e2"

  url "https://github.com/earendil-works/pi/releases/download/v#{version}/pi-darwin-#{arch}.tar.gz"
  name "Pi"
  desc "Extensible terminal coding agent"
  homepage "https://pi.dev/"

  depends_on :macos

  generated_script "repair-signature.sh", content: <<~SH
    #!/bin/sh
    set -eu
    executable="$1"

    if /usr/bin/codesign --verify "$executable" >/dev/null 2>&1; then
      exit 0
    fi

    # Repair invalid ad-hoc signatures only; do not replace publisher identities.
    signature=$(/usr/bin/codesign --display --verbose "$executable" 2>&1)
    case "$signature" in
      *Signature=adhoc*) /usr/bin/codesign --force --sign - "$executable" ;;
      *) printf '%s\\n' 'Pi has an unexpected invalid signature; installation stopped.' >&2; exit 1 ;;
    esac
    /usr/bin/codesign --verify "$executable"
  SH

  binary "pi/pi"

  postflight_steps do
    run "{{staged_path}}/repair-signature.sh", args: ["{{staged_path}}/pi/pi"]
  end

  caveats <<~EOS
    Update the Pi executable with `brew upgrade pi`, not Pi's self-updater.
  EOS
end
