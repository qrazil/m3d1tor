# sourced by tests/test.sh: unit programs
for t in t_app t_buffer t_key t_register t_text; do
    unit "$t"
done
