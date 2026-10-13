# sourced by tests/test.sh: unit programs
for t in t_app t_keymap t_buffer t_fuzzy t_grep t_git t_ignore t_key t_map t_picker t_register t_surround t_syntax t_text t_tree t_window; do
    unit "$t"
done
