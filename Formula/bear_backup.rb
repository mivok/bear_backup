class BearBackup < Formula
  desc "Bear backup utility"
  homepage "https://github.com/mivok/bear_backup"
  head "https://github.com/mivok/bear_backup.git", :using => :git

  depends_on "python3"

  def install
    bin.mkpath
    bin.install "bear_backup.py"
  end

  plist_options :manual => "bear_backup"

  def plist
    <<~EOS
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
        "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>#{plist_name}</string>
            <key>EnvironmentVariables</key>
            <dict>
                <key>PATH</key>
                <string>/bin:/usr/bin:/usr/local/bin</string>
            </dict>
            <key>ProgramArguments</key>
            <array>
                <string>#{HOMEBREW_PREFIX}/bin/bear_backup.py</string>
                <string>--notify</string>
                <string>--remove</string>
                <string>~/Dropbox/backups/bear</string>
            </array>
            <key>RunAtLoad</key>
            <false/>
            <key>StartCalendarInterval</key>
            <dict>
                <key>Hour</key>
                <integer>0</integer>
                <key>Minute</key>
                <integer>0</integer>
            </dict>
        </dict>
    </plist>
    EOS
  end

  test do
    system bin/"bear_backup.py", "--help"
  end
end
