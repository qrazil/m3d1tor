# sourced by tests/test.sh: unit programs
for t in t_app t_buffer t_fuzzy t_grep t_ignore t_key t_picker t_register t_text; do
    unit "$t"
done
