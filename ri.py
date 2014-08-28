import sublime, sublime_plugin
import platform
import subprocess

OUTPUT_VIEW_NAME = 'ri Result'
""" 

This is internal command.
Don't execute directly!
"""
class RiRunCommand(sublime_plugin.TextCommand):
  def run(self, edit, setting, text):
    output_view = self.view
    
    # verify that runing on collect output view
    if output_view.name() != OUTPUT_VIEW_NAME:
      sublime.error_message("RiRunCommand on View that name is not %s!" % OUTPUT_VIEW_NAME)
      return
    
    scroll_pos = output_view.size()
    output_view.set_read_only(False)
    
    # Build command string
    cmd_buf = []
    ssh_setting = setting.get('ssh', None)
    if ssh_setting:
      # Build ssh query
      cmd_buf.append("ssh ")
      
      key = ssh_setting.get('key', None)
      if key:
        cmd_buf.append("-i \'%s\' " % key)
        
      user = ssh_setting.get('user', None) 
      if user:
        cmd_buf.append("%s@", user)
      
      host = ssh_setting.get('host', None)
      if not host:
        sublime.error_message("Not specified host in current ssh setting!")
        return
        
      cmd_buf.append("%s " % host)
    
    cmd_buf.append("ri -T --format=markdown --width=100 '%s'" % text)
    cmd_string = "".join(cmd_buf)
    
    # Execute ri command
    try:
      result_text = subprocess.check_output(cmd_string, universal_newlines = True)
    except subprocess.CalledProcessError as e:
      print("command ``%s'' returned non-zero exit status %d" % (cmd_string, e.returncode))
      print("output is here:")
      print(e.output)
      sublime.error_message("ri command exit with error!\nSee console for more detail.")
      return
    
    # Insert result to output view
    output_view.set_read_only(False)
    output_view.insert(edit, 0, result_text + "\n\n\n")
    output_view.set_read_only(True)
    
    # Scroll to result
    output_view.show(0, True)
    output_view.sel().clear()
    output_view.sel().add(sublime.Region(0))
    output_view.window().focus_view(output_view)
    
  
""" Input search word in input panel


"""
class RiInputCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("called")
    msg = "Input ri search word"
    view = self.view
    
    sel = view.sel()[0]
    if not sel.empty():
      value = view.substr(sel)
    else:
      value = ""
      
    view.window().show_input_panel(msg, value, self.on_done, None, None)
  
  """ Callback for 'show_input_panel' at 'run' method
  
  Call 'ri_command' with input text
  """  
  def on_done(self, text):
    self.view.run_command('ri', { 'text': text })
    
""" Main part of this plugin
  
  - Load and select collect setting.
  - Open output view.
  - Execute ri by run 'ri_run_command' on output view
"""
class RiCommand(sublime_plugin.TextCommand):
  def run(self, edit, text = ''):
    # Load settings
    settings = sublime.load_settings("ri.sublime-settings")
    
    # Select settings for current environment
    case_settings = settings.get('case', {})
    
    # Use corresponding setting or default setting
    setting = case_settings.get(platform.node())
    if not setting:
      setting = settings.get('default', {})
    
    # Search or open output view
    for view in self.view.window().views():
      if view.name() == OUTPUT_VIEW_NAME:
        output_view = view
        break
    else:
      output_view = sublime.active_window().new_file()
      output_view.set_scratch(True)
      output_view.set_name(OUTPUT_VIEW_NAME)
      syntax = setting.get('syntax', "Packages/Markdown/Markdown.tmLanguage")
    
    # Now,  run 'ri_run_command' on output view
    output_view.run_command('ri_run', { 'setting': setting, 'text': text })
    