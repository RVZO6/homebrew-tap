cask "pi" do
  arch arm: "arm64", intel: "x64"

  version "1.5.1"
  sha256 arm: "eecbee4fbb6128c625ba44ffe30cfc15884a7791d242017ba9378f57485971d5",
         intel: "9fa62a4fb68b7036c151a1c6128d8a91dd4f83f451f6b33e479ea7cb6de1a026"

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
