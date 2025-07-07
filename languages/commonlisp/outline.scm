(list_lit
    .
    (sym_lit) @start-symbol @context
    .
    [
        (sym_lit) @name
        (list_lit . (sym_lit) @name)
    ]
    (#match? @start-symbol "^(defun|defvar|defparameter|defconstant|defmacro|defclass|defgeneric|defmethod|defpackage)$")
) @item
