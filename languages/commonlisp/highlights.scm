["(" ")"] @punctuation.bracket

(str_lit) @string
(char_lit) @constant.builtin

[(comment)] @comment

(sym_lit) @variable
(kwd_lit) @constant

(num_lit) @number
(nil_lit) @constant.builtin

; Function calls - first symbol in list
(list_lit
  .
  (sym_lit) @function)

; Common Lisp special forms and macros
(list_lit
  .
  (sym_lit) @keyword
  (#match? @keyword
   "^(defun|defvar|defparameter|defconstant|defmacro|defclass|defgeneric|defmethod|defpackage|in-package|use-package|export|import|if|when|unless|cond|case|loop|do|dotimes|dolist|let|let\\*|flet|labels|macrolet|symbol-macrolet|lambda|function|and|or|not|declare|declaim|proclaim|make-instance|slot-value|quote|backquote|unquote|unquote-splicing|setf|setq|push|pop|incf|decf|multiple-value-bind|multiple-value-call|multiple-value-list|multiple-value-setq|values|return|return-from|block|tagbody|go|catch|throw|unwind-protect|handler-case|handler-bind|restart-case|restart-bind|with-open-file|with-input-from-string|with-output-to-string|eval-when|load-time-value|locally|the|check-type|assert|error|warn|cerror|break|ignore-errors|with-slots|with-accessors|defstruct|typecase|etypecase|ctypecase)$"
   ))

; NIL and T
((sym_lit) @constant.builtin
 (#match? @constant.builtin "^(nil|t)$"))

; Keywords (start with :)
((kwd_lit) @constant)
