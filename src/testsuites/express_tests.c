/**
 * @file
 *
 * @brief Express tests routings
 *
 * @date Dec 4, 2008
 *
 * @author Anton Bondarev
 *         - Initial implementation
 * @author Eldar Abusalimov
 *         - Reworking finding handler algorithm
 * @author Alexey Fomin
 *         - Adding level implementation code
 */

#include <common.h>
#include <express_tests.h>
#include <kernel/init.h>
#include <kernel/sys.h>

typedef int (*express_tests_criterion_func_t)(express_test_descriptor_t *);

static int execute_level = 0;
static int is_on_level(express_test_descriptor_t *expr_tst) {
	return expr_tst->level == execute_level;
}

static int always_true(express_test_descriptor_t *expr_tst) {
	return 1;
}

static int express_tests_execute_on_criterion( express_tests_criterion_func_t has_to_be_executed ) {
	extern int *__express_tests_result;
	extern express_test_descriptor_t *__express_tests_start, *__express_tests_end;
	express_test_descriptor_t ** p_test = &__express_tests_start;
	int i, total = (int) (&__express_tests_end - &__express_tests_start);
	int passed = 0, failed = 0, skipped = 0, result;

	for (i = 0; i < total; i++, p_test++) {
		if (NULL == (*p_test)) {
			LOG_ERROR("Missing express test descriptor\n");
			continue;
		}
		if (NULL == ((*p_test)->name)) {
			LOG_ERROR("Broken express test descriptor: can't find test name\n");
			continue;
		}
		if (NULL == ((*p_test)->exec)) {
			LOG_ERROR("Broken express test descriptor: can't find exec function for test %s\n", (*p_test)->name);
			continue;
		}
		if (!has_to_be_executed(*p_test)) {
			continue;
		}

		TRACE("Running express test: %s ... ", (*p_test)->name);
		if (!(*p_test)->execute_on_boot)
		{
			TRACE("SKIPPED\n");
			skipped++;
			continue;
		}

		/* Executing express test */
		result = (*p_test)->exec(0, NULL);

		/* writing test results to special section */
		__express_tests_result[i] = result;

		if (result == EXPRESS_TESTS_PASSED_RETCODE) {
			TRACE("PASSED\n");
			passed++;
		} else if (result == EXPRESS_TESTS_FAILED_RETCODE) {
			TRACE("FAILED\n");
			failed++;
		} else if (result == EXPRESS_TESTS_INTERRUPTED_RETCODE) {
			TRACE("INTERRUPTED\n");
			failed++;
		} else if (result == EXPRESS_TESTS_UNABLE_TO_START_RETCODE) {
			TRACE("UNABLE TO START\n");
			failed++;
		} else {
			TRACE(" Unknown retcode: %i (counting FAILED)\n", result);
			failed++;
		}
	}

	if (passed + failed == 0) {
		/* No tests to execute on this level
		 * Nothing to write in this case */
		return 0;
	}

	TRACE("\nTests results:\n");
	TRACE("\tSkipped: %d\n", skipped);
	TRACE("\t Passed: %d\n", passed);
	TRACE("\t Failed: %d\n", failed);

	return (failed == 0) ? 0 : -1;
}


void express_tests_execute( int level ) {
	execute_level = level;
	express_tests_execute_on_criterion(is_on_level);
}

void express_tests_execute_all() {
	express_tests_execute_on_criterion(always_true);
}
