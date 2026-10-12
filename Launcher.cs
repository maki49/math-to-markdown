using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

internal static class Launcher
{
    [STAThread]
    private static void Main()
    {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        string python = Path.Combine(root, @".venv312\Scripts\pythonw.exe");
        string app = Path.Combine(root, "app.py");
        if (!File.Exists(python) || !File.Exists(app))
        {
            MessageBox.Show("Please keep the entire project folder and run setup.cmd first.", "Math to Markdown");
            return;
        }
        try
        {
            ProcessStartInfo start = new ProcessStartInfo(python, "\"" + app + "\"");
            start.WorkingDirectory = root;
            start.UseShellExecute = false;
            start.CreateNoWindow = true;
            Process.Start(start);
        }
        catch (Exception error)
        {
            MessageBox.Show(error.Message, "Math to Markdown");
        }
    }
}
