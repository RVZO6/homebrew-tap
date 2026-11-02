cask "pi" do
  arch arm: "arm64", intel: "x64"

  version "1.5.0"
  sha256 arm: "a9bf0d82d58d2a7d337f4ae4171b5fc9ebffe42509527a831364c4b65adf2cdf",
         intel: "f41b26cd9a1754abe259e05a421fb33b00936779cb0783c893a6389d1bd2ee0d"

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
