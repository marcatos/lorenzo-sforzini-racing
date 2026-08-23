using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Windows.Forms;

namespace SMarcato42Screensaver;

static class Program
{
    [STAThread]
    static void Main(string[] args)
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);

        string mode = "/s";
        if (args.Length > 0)
            mode = args[0].ToLowerInvariant();

        if (mode.StartsWith("/c"))
        {
            MessageBox.Show(
                "S.Marcato 42 Racing Screensaver\n\n" +
                "Slideshow branded con logo al centro.\n" +
                "Esci: muovi il mouse o premi un tasto.",
                "S.Marcato 42",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information);
            return;
        }

        if (mode.StartsWith("/p"))
        {
            // Preview in tiny control panel window — skip for simplicity
            return;
        }

        // /s or default: run fullscreen on all screens
        var forms = new List<SaverForm>();
        foreach (var screen in Screen.AllScreens)
        {
            var f = new SaverForm(screen.Bounds);
            forms.Add(f);
            f.Show();
        }
        Application.Run();
    }
}

sealed class SaverForm : Form
{
    readonly List<Image> _slides = new();
    readonly System.Windows.Forms.Timer _timer;
    int _index;
    float _fade; // 0..1
    bool _fading;
    Point _lastMouse = Point.Empty;
    bool _mouseReady;
    const int HoldMs = 7000;
    const int FadeMs = 1200;
    DateTime _phaseStart = DateTime.UtcNow;

    public SaverForm(Rectangle bounds)
    {
        FormBorderStyle = FormBorderStyle.None;
        Bounds = bounds;
        StartPosition = FormStartPosition.Manual;
        TopMost = true;
        BackColor = Color.FromArgb(8, 8, 10);
        DoubleBuffered = true;
        ShowInTaskbar = false;
        Cursor.Hide();
        KeyPreview = true;

        LoadSlides();

        _timer = new System.Windows.Forms.Timer { Interval = 16 };
        _timer.Tick += (_, _) => Tick();
        _timer.Start();

        KeyDown += (_, _) => ExitAll();
        MouseMove += OnMouseMove;
        MouseDown += (_, _) => ExitAll();
        Click += (_, _) => ExitAll();
    }

    void LoadSlides()
    {
        string baseDir = Path.GetDirectoryName(Environment.ProcessPath)
            ?? AppContext.BaseDirectory;
        // Prefer slides next to the .scr, then known brand folders
        var candidates = new[]
        {
            Path.Combine(baseDir, "slides"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyPictures),
                "Wallpapers", "SMarcato42", "slideshow"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyPictures),
                "Wallpapers", "SMarcato42"),
        };

        var files = new List<string>();
        foreach (var dir in candidates)
        {
            if (!Directory.Exists(dir)) continue;
            files.AddRange(Directory.GetFiles(dir, "*.jpg"));
            files.AddRange(Directory.GetFiles(dir, "*.jpeg"));
            files.AddRange(Directory.GetFiles(dir, "*.png")
                .Where(f => Path.GetFileName(f).Contains("span", StringComparison.OrdinalIgnoreCase)
                         || Path.GetFileName(f).Contains("hero", StringComparison.OrdinalIgnoreCase)
                         || Path.GetFileName(f).StartsWith("01_", StringComparison.OrdinalIgnoreCase)
                         || Path.GetFileName(f).StartsWith("02_", StringComparison.OrdinalIgnoreCase)
                         || Path.GetFileName(f).StartsWith("03_", StringComparison.OrdinalIgnoreCase)
                         || Path.GetFileName(f).StartsWith("04_", StringComparison.OrdinalIgnoreCase)
                         || Path.GetFileName(f).StartsWith("05_", StringComparison.OrdinalIgnoreCase)));
            if (files.Count > 0) break;
        }

        files = files.Distinct(StringComparer.OrdinalIgnoreCase).OrderBy(f => f).ToList();
        foreach (var f in files)
        {
            try
            {
                // Clone into memory so files aren't locked
                using var img = Image.FromFile(f);
                _slides.Add(new Bitmap(img));
            }
            catch { /* skip bad file */ }
        }

        if (_slides.Count == 0)
        {
            // Fallback solid brand plate
            var bmp = new Bitmap(1920, 1080);
            using var g = Graphics.FromImage(bmp);
            g.Clear(Color.FromArgb(8, 8, 10));
            using var font = new Font("Segoe UI", 72, FontStyle.Bold | FontStyle.Italic);
            var text = "S.Marcato 42";
            var sz = g.MeasureString(text, font);
            g.DrawString(text, font, Brushes.WhiteSmoke,
                (bmp.Width - sz.Width) / 2f, (bmp.Height - sz.Height) / 2f);
            _slides.Add(bmp);
        }
    }

    void Tick()
    {
        var elapsed = (DateTime.UtcNow - _phaseStart).TotalMilliseconds;
        if (!_fading)
        {
            if (elapsed >= HoldMs && _slides.Count > 1)
            {
                _fading = true;
                _fade = 0f;
                _phaseStart = DateTime.UtcNow;
            }
        }
        else
        {
            _fade = Math.Min(1f, (float)(elapsed / FadeMs));
            if (_fade >= 1f)
            {
                _index = (_index + 1) % _slides.Count;
                _fading = false;
                _fade = 0f;
                _phaseStart = DateTime.UtcNow;
            }
        }
        Invalidate();
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        var g = e.Graphics;
        g.SmoothingMode = SmoothingMode.HighQuality;
        g.InterpolationMode = InterpolationMode.HighQualityBicubic;
        g.Clear(BackColor);

        if (_slides.Count == 0) return;

        var cur = _slides[_index];
        var next = _slides[(_index + 1) % _slides.Count];

        DrawCover(g, cur, ClientRectangle, _fading ? 1f - _fade : 1f);
        if (_fading)
            DrawCover(g, next, ClientRectangle, _fade);

        // Stronger carbon edge bands for footer/UI readability over bright photos
        int bandH = Math.Max(120, ClientSize.Height / 9);
        using (var topGrad = new LinearGradientBrush(
                   new Rectangle(0, 0, ClientSize.Width, bandH),
                   Color.FromArgb(160, 8, 8, 10),
                   Color.FromArgb(0, 8, 8, 10),
                   LinearGradientMode.Vertical))
        {
            g.FillRectangle(topGrad, 0, 0, ClientSize.Width, bandH);
        }
        using (var botGrad = new LinearGradientBrush(
                   new Rectangle(0, ClientSize.Height - bandH, ClientSize.Width, bandH),
                   Color.FromArgb(0, 8, 8, 10),
                   Color.FromArgb(190, 8, 8, 10),
                   LinearGradientMode.Vertical))
        {
            g.FillRectangle(botGrad, 0, ClientSize.Height - bandH, ClientSize.Width, bandH);
        }

        // Brand footer line
        using var pen = new Pen(Color.FromArgb(140, 248, 248, 250), 1);
        int cx = ClientSize.Width / 2;
        g.DrawLine(pen, cx - 72, ClientSize.Height - 56, cx + 72, ClientSize.Height - 56);
        using var tiny = new Font("Segoe UI", 11, FontStyle.Regular);
        var label = "S.MARCATO 42  ·  RACING";
        var lsz = g.MeasureString(label, tiny);
        g.DrawString(label, tiny, new SolidBrush(Color.FromArgb(200, 248, 248, 250)),
            cx - lsz.Width / 2f, ClientSize.Height - 48);
    }

    static void DrawCover(Graphics g, Image img, Rectangle target, float opacity)
    {
        if (opacity <= 0.01f) return;
        float scale = Math.Max(target.Width / (float)img.Width, target.Height / (float)img.Height);
        int w = (int)(img.Width * scale);
        int h = (int)(img.Height * scale);
        int x = target.X + (target.Width - w) / 2;
        int y = target.Y + (target.Height - h) / 2;

        if (opacity >= 0.99f)
        {
            g.DrawImage(img, x, y, w, h);
            return;
        }

        var cm = new ColorMatrix { Matrix33 = opacity };
        using var ia = new ImageAttributes();
        ia.SetColorMatrix(cm);
        g.DrawImage(img, new Rectangle(x, y, w, h), 0, 0, img.Width, img.Height, GraphicsUnit.Pixel, ia);
    }

    void OnMouseMove(object? sender, MouseEventArgs e)
    {
        if (!_mouseReady)
        {
            _lastMouse = e.Location;
            _mouseReady = true;
            return;
        }
        int dx = Math.Abs(e.X - _lastMouse.X);
        int dy = Math.Abs(e.Y - _lastMouse.Y);
        if (dx > 8 || dy > 8) ExitAll();
    }

    static void ExitAll()
    {
        Cursor.Show();
        Application.Exit();
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            _timer.Stop();
            _timer.Dispose();
            foreach (var s in _slides) s.Dispose();
            _slides.Clear();
        }
        base.Dispose(disposing);
    }
}
