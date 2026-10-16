cask "pi" do
  arch arm: "arm64", intel: "x64"

  version "1.3.0"
  sha256 arm: "1f9ae61cdeae04dd68caf1a1e8ab8ec9b292062f6ccb3252e0a9cbe93b5b16f1",
         intel: "9ff562e2e439f50971b1f6bd9b62b30946600d9e9baa4ea19635cf630a553066"

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
