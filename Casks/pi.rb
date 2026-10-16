cask "pi" do
  arch arm: "arm64", intel: "x64"

  version :latest
  sha256 :no_check

  url "https://github.com/earendil-works/pi/releases/latest/download/pi-darwin-#{arch}.tar.gz"
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
    run "repair-signature.sh", args: ["{{staged_path}}/pi/pi"]
  end

  caveats <<~EOS
    Update the Pi executable with `brew upgrade pi`, not Pi's self-updater.
    To include Pi in a general `brew upgrade`, add
    HOMEBREW_UPGRADE_GREEDY_CASKS=pi to your Homebrew environment file.
  EOS
end
